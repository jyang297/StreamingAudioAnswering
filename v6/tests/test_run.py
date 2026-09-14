import copy
import sqlite3

import pytest

from multitable_poc.database import SQLiteCatalog
from multitable_poc.run import run_case, validate_schedule, summarize


@pytest.mark.parametrize("schedule", [None, {},
    {"source_label": "scripted", "final_at_ms": 10, "snapshots": [{"at_ms": 11, "text": "late"}]},
    {"source_label": "scripted", "final_at_ms": float("nan"), "snapshots": []},
    {"source_label": "scripted", "final_at_ms": 10, "snapshots": [{"at_ms": -2, "text": "negative"}]},
    {"source_label": "scripted", "final_at_ms": 10, "snapshots": [{"at_ms": -.5, "text": "negative"}]},
])
def test_invalid_schedule_cannot_invent_or_backdate_timings(schedule):
    with pytest.raises(ValueError):
        validate_schedule(schedule)


@pytest.mark.asyncio
async def test_runner_uses_reference_only_after_online_query(tmp_path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript("CREATE TABLE a(id INTEGER, label TEXT); CREATE TABLE b(parent INTEGER, n INTEGER);"
                           "INSERT INTO a VALUES(1,'alpha'); INSERT INTO b VALUES(1,4);")
    catalog = SQLiteCatalog(path, "fixture")
    sql = "SELECT a.label, b.n FROM a JOIN b ON a.id=b.parent"
    case = {"db_id": "fixture", "question_id": "1", "question": "List labels and amounts",
            "SQL": sql + " -- GOLD_ONLY_MARKER", "original_SQL": "OLD_GOLD_MARKER", "evidence": "FINAL_HINT_ONLY"}
    class OracleForWiringOnly:
        metrics = []
        calls = []
        async def call(self, role, instruction, payload):
            self.calls.append(copy.deepcopy(payload))
            self.metrics.append({"role": role, "elapsed_ms": 0})
            return {"action": "retrieve", "query": {"sql": sql}}
    endpoint = OracleForWiringOnly()
    try:
        record = await run_case(case, "final-only", endpoint, catalog)
        assert record["outcome"] == "nonempty_result_agreement"
        assert record["path"] == "demand"
        assert len(record["database_calls"]) == 1
        assert len(record["http_calls"]) == 1
        assert "GOLD_ONLY_MARKER" not in str(endpoint.calls)
        assert "OLD_GOLD_MARKER" not in str(endpoint.calls)
        assert "FINAL_HINT_ONLY" not in str(endpoint.calls)
        assert record["post_final_retrieval_ms"] >= 0
        assert record["semantic_correctness"] == "not_assessed"
    finally:
        await catalog.close()


def test_summary_does_not_count_empty_agreement_as_paired_quality():
    base = {"case_id": "fixture:1", "outcome": "empty_result_agreement", "path": "demand",
            "http_calls": [], "post_final_retrieval_ms": 100, "reuse_reference_disagreement": False}
    report = summarize([{**base, "arm": "final-only"}, {**base, "arm": "speculative", "path": "reuse_ready"}])
    assert report["paired_nonempty_agreement"] == []
    assert report["paired_saved_ms_median"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("arm", ["final-only", "speculative"])
async def test_answer_repair_cannot_hide_wrong_initial_retrieval(tmp_path, arm):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript("CREATE TABLE a(id INTEGER); CREATE TABLE b(parent INTEGER,n INTEGER);"
                           "INSERT INTO a VALUES(1); INSERT INTO b VALUES(1,4);")
    catalog = SQLiteCatalog(path, "fixture")
    correct = "SELECT b.n FROM a JOIN b ON a.id=b.parent"
    wrong = "SELECT b.n+1 FROM a JOIN b ON a.id=b.parent"
    class RepairingOracle:
        def __init__(self):
            self.metrics = []
        async def call(self, role, instruction, payload):
            self.metrics.append({"role": role})
            if role == "builder":
                return {"action": "retrieve", "query": {"sql": wrong}}
            if role == "checker":
                return {"candidate_id": payload["candidates"][0]["id"]}
            if payload["can_rewrite"]:
                return {"action": "retrieve", "query": {"sql": correct}}
            return {"action": "answer", "text": "Repaired evidence, not an assessed answer."}
    try:
        record = await run_case({"db_id": "fixture", "question_id": "repair", "question": "What is n?", "SQL": correct},
            arm, RepairingOracle(), catalog, answer=True, min_interval_ms=0,
            schedule={"source_label": "scripted wiring test", "final_at_ms": 200,
                      "snapshots": [{"at_ms": 0, "text": "What is n?"}]})
        assert record["outcome"] == "result_mismatch"
        assert record["answer_evidence_comparison"]["status"] == "nonempty_result_agreement"
        assert record["returned_query"]["sql"] == wrong
        assert record["answer_evidence_query"]["sql"] == correct
        if arm == "speculative":
            assert record["path"] == "reuse_ready"
            assert record["reuse_reference_disagreement"]
    finally:
        await catalog.close()
