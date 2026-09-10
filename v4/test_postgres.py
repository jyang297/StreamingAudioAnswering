import os

import httpx
import pytest

from rag_poc.database import PostgresCatalog
from rag_poc.endpoints import Answerer, Builder, JSONEndpoint, LLMChecker
from rag_poc.livekit_adapter import replay_session
from rag_poc.models import Query
from rag_poc.pipeline import Pipeline
from scripted_endpoint import transport


pytestmark = [pytest.mark.asyncio, pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires explicitly enabled local Docker fixture")]


async def connect():
    return await PostgresCatalog.connect(credential_file=os.environ.get("RAG_DB_CREDENTIAL_FILE"))


async def test_real_sql_filters_and_literal_values():
    db = await connect()
    try:
        rows = await db.search(Query(name="Chai"))
        assert rows[0]["product_id"] == 1
        assert rows[0]["unit_price"] == 18.0
        assert rows[0]["units_in_stock"] == 39
        cheap = await db.search(Query(max_price=10, discontinued=False, order="price_asc", limit=5))
        assert len(cheap) == 5
        assert all(r["unit_price"] <= 10 and not r["discontinued"] for r in cheap)
        assert [r["unit_price"] for r in cheap] == sorted(r["unit_price"] for r in cheap)
        assert await db.search(Query(name="%' OR true; DROP TABLE northwind_products; --")) == []
        assert await db.search(Query(name="%")) == []  # literal substring, not LIKE wildcard
        assert (await db.search(Query(name="Chai")))[0]["product_id"] == 1
    finally:
        await db.close()


@pytest.mark.parametrize("speculate", [False, True])
async def test_real_postgres_and_livekit_with_scripted_endpoint_contract(speculate):
    db = await connect()
    async with httpx.AsyncClient(transport=transport()) as client:
        ep = JSONEndpoint(base_url="http://scripted.test/v1", model="NO-REAL-LLM", client=client)
        p = Pipeline(Builder(ep), LLMChecker(ep), db, Answerer(ep), speculate=speculate, min_interval=0)
        try:
            result = await replay_session(p, [
                {"partials": ["Chai"], "final": "Chai", "gap_ms": 40},
                {"partials": ["stock?"], "final": "stock?", "gap_ms": 40},
                {"partials": ["Chai"], "final": "Chang", "gap_ms": 40},
                {"partials": [], "final": "unknown", "gap_ms": 0},
            ])
            assert result["stt_streams"] == 1
            assert result["audio_frames"] == 1
            assert [t["evidence"][0]["query"]["name"] for t in result["turns"][:3]] == ["Chai", "Chai", "Chang"]
            assert not result["turns"][-1]["evidence"]
            assert result["turns"][-1]["answer"] == "SCRIPTED ANSWER FROM SQL: []"
            assert len([m for m in result["history"] if m["role"] == "assistant"]) == 4
            assert all(t["answer"] for t in result["turns"])
            assert all(m["status"] == "ok" for m in ep.metrics)
            assert len(db.metrics) == (4 if speculate else 3)
            assert result["turns"][0]["path"] in (("reuse_ready", "reuse_wait") if speculate else ("demand",))
        finally:
            await p.close()
            await db.close()
