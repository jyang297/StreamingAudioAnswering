import asyncio
import copy
import sqlite3

import pytest

from multitable_poc.database import SQLiteCatalog
from multitable_poc.endpoints import Builder, Checker, Answerer
from multitable_poc.pipeline import MultiTablePipeline


@pytest.mark.asyncio
async def test_real_multitable_reuse_then_final_correction(tmp_path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as c:
        c.executescript("CREATE TABLE person(id INTEGER, name TEXT); CREATE TABLE membership(person_id INTEGER, team_id INTEGER);"
                        "CREATE TABLE team(id INTEGER, name TEXT); INSERT INTO person VALUES(1,'Ada');"
                        "INSERT INTO membership VALUES(1,2); INSERT INTO team VALUES(2,'Research');")
    catalog = SQLiteCatalog(path, "fixture")
    sql = "SELECT t.name FROM person p JOIN membership m ON p.id=m.person_id JOIN team t ON t.id=m.team_id WHERE p.name='Ada'"
    final_sql = sql + " AND t.name='Sales'"
    calls = []
    class ScriptedEndpoint:
        async def call(self, role, instruction, payload):
            calls.append((role, copy.deepcopy(payload)))
            if role == "builder":
                return {"action": "retrieve", "query": {"sql": final_sql if "Sales" in payload["text"] else sql}}
            if role == "checker":
                return {"candidate_id": None if "Sales" in payload["final_text"] else payload["candidates"][0]["id"]}
            return {"action": "answer", "text": "Scripted answer; wiring test only."}
    endpoint = ScriptedEndpoint()
    pipeline = MultiTablePipeline(Builder(endpoint, catalog), Checker(endpoint, catalog), catalog,
        Answerer(endpoint, catalog), speculate=True, min_interval=0, max_builder_calls=2)
    try:
        for text, expected in [("Which team is Ada in?", "reuse_ready"), ("Is Ada in Sales?", "demand")]:
            pipeline.start_turn([])
            pipeline.observe("Which team is Ada in?")
            for _ in range(200):
                if any(c.retrieval and c.retrieval.done() for c in pipeline.candidates):
                    break
                await asyncio.sleep(.005)
            bundle = await pipeline.finish(text)
            assert bundle.path == expected
            final_calls = [payload for role, payload in calls if role == "builder" and payload["final"]]
            assert final_calls[-1]["previous_queries"] == []
            if expected == "reuse_ready":
                assert bundle.evidence[0].rows[0]["values"] == ["Research"]
            else:
                assert bundle.evidence[0].rows == []
            await pipeline.answer(bundle)
        assert all("time_spent_ms" in item for item in pipeline.timings)
        assert any(item["step"] == "final_query_builder" for item in pipeline.timings)
        assert len([payload for role, payload in calls if role == "builder" and payload["final"]]) == 2
    finally:
        assert await pipeline.close() == 0
        await catalog.close()
