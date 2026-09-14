import asyncio
import copy
import json
import sqlite3

import httpx
import pytest

from multitable_poc.database import SQLiteCatalog
from multitable_poc.endpoints import Builder, Checker, Answerer, JSONEndpoint
from multitable_poc.models import ContractError
from multitable_poc.compat import BasePipeline
from rag_poc.models import Evidence


@pytest.fixture
def catalog(tmp_path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as c:
        c.executescript("CREATE TABLE parent(id INTEGER PRIMARY KEY, name TEXT);"
                        "CREATE TABLE child(id INTEGER, parent_id INTEGER REFERENCES parent(id), amount REAL);"
                        "INSERT INTO parent VALUES(1,'Alpha'); INSERT INTO child VALUES(2,1,12.5);")
    return SQLiteCatalog(path, "fixture")


class Capture:
    def __init__(self, result):
        self.result, self.calls = result, []

    async def call(self, role, instruction, payload):
        self.calls.append((role, instruction, copy.deepcopy(payload)))
        return self.result


@pytest.mark.asyncio
async def test_builder_uses_actual_schema_and_independent_final(catalog):
    endpoint = Capture({"action": "retrieve", "query": {"sql":
        "SELECT p.name, SUM(c.amount) FROM parent p JOIN child c ON c.parent_id=p.id GROUP BY p.id"}})
    builder = Builder(endpoint, catalog)
    result = await builder.build("Total amount for each parent?", [], [{"sql": "future hypothesis"}], final=True)
    payload = endpoint.calls[0][2]
    assert {t["name"] for t in payload["schema"]["tables"]} == {"parent", "child"}
    assert payload["previous_queries"] == []
    assert "benchmark_evidence" not in payload and "gold_sql" not in payload and "SQL" not in payload
    assert result.query.db_id == "fixture"
    assert (await catalog.search(result.query))[0]["values"] == ["Alpha", 12.5]
    assert builder.records[0]["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_evidence_is_explicit(catalog):
    endpoint = Capture({"action": "wait", "query": None})
    builder = Builder(endpoint, catalog, benchmark_evidence="unit mapping")
    await builder.build("Incomplete", [], [], final=False)
    assert "benchmark_evidence" not in endpoint.calls[0][2]
    await builder.build("Complete", [], [], final=True)
    assert endpoint.calls[1][2]["benchmark_evidence"] == "unit mapping"


@pytest.mark.asyncio
async def test_answer_rejects_cross_database_evidence(catalog):
    from dataclasses import replace
    query = replace(catalog.validate("SELECT * FROM parent"), db_id="other")
    endpoint = Capture({"action": "answer", "text": "must not run"})
    with pytest.raises(ContractError, match="another database"):
        await Answerer(endpoint, catalog).respond("All", [], [Evidence(query, [])], can_rewrite=False)
    assert endpoint.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("query", [{"sql": "SELECT * FROM parent", "db_id": "other"}, {"sql": "SELECT invented FROM parent"}])
async def test_model_cannot_select_scope_or_invent_columns(catalog, query):
    with pytest.raises(ContractError):
        await Builder(Capture({"action": "retrieve", "query": query}), catalog).build("Query", [], [], final=True)


@pytest.mark.asyncio
async def test_checker_filters_database_and_schema_before_endpoint(catalog):
    query = catalog.validate("SELECT * FROM parent")
    good = {"id": 3, "query": query.json(), "completed": True}
    bad_db = {"id": 1, "query": {**query.json(), "db_id": "other"}, "completed": True}
    bad_schema = {"id": 2, "query": {**query.json(), "schema_id": "old"}, "completed": True}
    endpoint = Capture({"candidate_id": 3})
    checker = Checker(endpoint, catalog)
    assert await checker.select("All parents", [], query, [bad_db, bad_schema]) is None
    assert endpoint.calls == []
    assert await checker.select("All parents", [], query, [bad_db, bad_schema, good]) == 3
    assert endpoint.calls[0][2]["candidates"] == [good]


@pytest.mark.asyncio
@pytest.mark.parametrize("selected", [True, "1", 99])
async def test_checker_rejects_invalid_selection(catalog, selected):
    query = catalog.validate("SELECT * FROM parent")
    with pytest.raises(ContractError):
        await Checker(Capture({"candidate_id": selected}), catalog).select("All", [], query,
            [{"id": 1, "query": query.json(), "completed": True}])


@pytest.mark.asyncio
async def test_answer_evidence_preserves_duplicate_columns_and_exposes_truncation(catalog):
    query = catalog.validate("SELECT p.id, c.id FROM parent p JOIN child c ON p.id=c.parent_id")
    rows = await catalog.search(query)
    endpoint = Capture({"action": "answer", "text": "Partial evidence only."})
    await Answerer(endpoint, catalog, max_evidence_rows=1).respond("IDs", [],
        [Evidence(query, rows * 2)], can_rewrite=False)
    item = endpoint.calls[0][2]["evidence"][0]
    assert item["columns"] == ["id", "id"]
    assert item["rows"] == [[1, 2]]
    assert item["truncated"] and item["total_rows"] == 2 and item["shown_rows"] == 1


@pytest.mark.asyncio
async def test_answer_rewrite_still_validates_and_respects_permission(catalog):
    response = {"action": "retrieve", "query": {"sql": "DELETE FROM parent"}}
    for permitted in (False, True):
        with pytest.raises(ContractError):
            await Answerer(Capture(response), catalog).respond("All", [], [], can_rewrite=permitted)


@pytest.mark.asyncio
async def test_http_budget_and_complete_json():
    bodies = []
    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message":
            {"content": '{"action":"wait","query":null}'}}], "usage": {"total_tokens": 7}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        endpoint = JSONEndpoint(base_url="https://example.test/v1", model="test", client=client, max_calls=1)
        result = await endpoint.call("builder", "Return JSON", {"text": "test"})
        assert result["action"] == "wait"
        assert bodies[0]["max_tokens"] == 2048
        with pytest.raises(RuntimeError, match="budget"):
            await endpoint.call("builder", "Return JSON", {})
        assert len(bodies) == 1 and endpoint.metrics[0]["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_truncated_json_rejected_even_when_syntax_is_valid():
    def handler(request):
        return httpx.Response(200, json={"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        endpoint = JSONEndpoint(base_url="https://example.test", model="test", client=client)
        with pytest.raises(ContractError, match="complete"):
            await endpoint.call("builder", "Return JSON", {})
        assert endpoint.metrics[0]["status"] == "error"
