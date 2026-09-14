import asyncio
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from multitable_poc import evaluation


def rows(*values, columns=None):
    columns = columns or ["value"]
    return [{"columns": list(columns), "values": list(value)} for value in values]


def test_unordered_comparison_preserves_duplicates_and_column_positions():
    assert evaluation.compare_rows(rows((1,), (2,), (1,)), rows((1,), (1,), (2,)))["result_equal"]
    assert not evaluation.compare_rows(rows((1,), (2,), (1,)), rows((1,), (2,), (2,)))["result_equal"]
    assert not evaluation.compare_rows(rows((1, 2), columns=["x", "x"]), rows((2, 1), columns=["x", "x"]))["result_equal"]


def test_aliases_ignored_but_width_and_requested_order_preserved():
    actual = rows((1, 2), columns=["same", "same"])
    expected = rows((1, 2), columns=["left", "right"])
    assert evaluation.compare_rows(actual, expected)["result_equal"]
    assert not evaluation.compare_rows(actual, rows((1,), columns=["same"]))["result_equal"]
    assert not evaluation.compare_rows(rows((1,), (2,)), rows((2,), (1,)), ordered=True)["result_equal"]


def test_numeric_comparison_is_exact_without_text_coercion():
    assert evaluation.compare_rows(rows((1,)), rows((1.0,)))["result_equal"]
    assert not evaluation.compare_rows(rows((1.0,)), rows((1.000000001,)))["result_equal"]
    assert not evaluation.compare_rows(rows((1,)), rows(("1",)))["result_equal"]
    assert not evaluation.compare_rows(rows((None,)), rows((0,)))["result_equal"]


def test_empty_result_agreement_does_not_claim_shape_or_semantics():
    comparison = evaluation.compare_rows([], [])
    assert comparison["status"] == "empty_result_agreement"
    assert comparison["shape_status"] == "shape_unassessed"
    assert comparison["shape_assessed"] is False
    assert comparison["semantic_correctness"] == "not_assessed"
    assert not evaluation.compare_rows([], rows((None,)))["result_equal"]


@pytest.mark.parametrize("actual", [
    [{"id": 1}],
    [{"columns": ["a", "b"], "values": [1]}],
    [{"columns": ["a"], "values": [1]}, {"columns": ["b"], "values": [2]}],
    [{"columns": ["a"], "values": [{"nested": "object"}]}],
])
def test_invalid_result_protocol_is_reported(actual):
    assert evaluation.compare_rows(actual, rows((1,)))["status"] == "protocol_error"


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "dataset"
    data = root / ".data"
    db_dir = data / "databases" / "financial"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "financial.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE author(id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE book(id INTEGER PRIMARY KEY, author_id INTEGER REFERENCES author(id), title TEXT);
            CREATE TABLE sale(book_id INTEGER REFERENCES book(id), amount INTEGER);
            INSERT INTO author VALUES (1, 'Mira'), (2, 'Owen');
            INSERT INTO book VALUES (1, 1, 'A'), (2, 1, 'B'), (3, 2, 'C');
            INSERT INTO sale VALUES (1, 10), (1, 10), (2, 30);
        """)
    records = [
        {"db_id": "financial", "question_id": "fixture-join", "question": "Mira sales?",
         "evidence": "Amounts are per sale.",
         "SQL": "SELECT a.name, s.amount FROM author a JOIN book b ON a.id=b.author_id JOIN sale s ON b.id=s.book_id WHERE a.name='Mira'"},
        {"db_id": "financial", "question_id": "fixture-empty", "question": "Unknown author?",
         "evidence": None, "SQL": "SELECT name FROM author WHERE name='unknown'"},
        {"db_id": "financial", "question_id": "fixture-clock", "question": "Current year?",
         "evidence": "", "SQL": "SELECT strftime('%Y', 'now') AS year"},
    ]
    (data / "arcwise-plat.json").write_text(json.dumps(records))
    (root / "selected-cases.json").write_text(json.dumps(records))
    return root, db_path, records


def test_load_preserves_complete_source_and_rejects_stale_selection(dataset):
    root, _, records = dataset
    assert evaluation.load_cases(root) == records
    altered = [dict(record) for record in records]
    altered[0]["evidence"] = "different business rule"
    (root / "selected-cases.json").write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="differs"):
        evaluation.load_cases(root)


def test_independent_reference_preserves_duplicates_and_duplicate_names(dataset):
    _, path, _ = dataset
    actual = evaluation._execute_reference(path, "SELECT b.id, s.book_id AS id FROM book b JOIN sale s ON b.id=s.book_id WHERE b.id=1")
    assert actual == rows((1, 1), (1, 1), columns=["id", "id"])
    with pytest.raises(sqlite3.DatabaseError):
        evaluation._execute_reference(path, "DELETE FROM book")
    with pytest.raises(sqlite3.DatabaseError):
        evaluation._execute_reference(path, "SELECT load_extension('never-load')")


def test_dataset_check_against_real_adapter_and_exclusive_output(dataset, tmp_path):
    root, _, _ = dataset
    output = tmp_path / "adapter-check"
    report = asyncio.run(evaluation.check_dataset(root, output))
    assert report["cases"] == report["adapter_execution_ok"] == report["reference_execution_ok"] == 3
    assert report["statuses"] == {"nonempty_result_agreement": 2, "empty_result_agreement": 1}
    assert report["clock_dependent_cases"] == 1
    assert report["short_question_join_cases"] == 1
    assert report["endpoints_called"] == 0 and report["model_accuracy"] == "not_measured"
    assert report["database_hashes"]["financial"]
    assert report["source_hashes"][".data/arcwise-plat.json"]
    observations = json.loads((output / "cases.json").read_text())
    assert all("SQL" not in observation for observation in observations)
    before = (output / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        asyncio.run(evaluation.check_dataset(root, output))
    assert (output / "summary.json").read_bytes() == before


def test_independent_reference_catches_wrong_adapter_result(dataset, tmp_path, monkeypatch):
    class WrongAdapter:
        def validate(self, sql):
            return SimpleNamespace(sql=sql, schema_id="fixture-schema")

        async def search(self, query):
            return rows((999,))

        async def close(self):
            pass

    monkeypatch.setattr(evaluation, "make_catalog", lambda *args: WrongAdapter())
    report = asyncio.run(evaluation.check_dataset(dataset[0], tmp_path / "wrong-adapter"))
    assert report["reference_execution_ok"] == 3
    assert report["statuses"] == {"result_mismatch": 3}
