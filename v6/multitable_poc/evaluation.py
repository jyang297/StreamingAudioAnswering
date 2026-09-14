"""Offline adapter checks against independent, read-only source-SQL execution.

Reference SQL belongs only to this evaluator. It is never an endpoint payload.
An agreement on one database snapshot is not a proof of SQL or model semantics.
"""
from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import sqlite3
import time
from typing import Any

import sqlglot
from sqlglot import exp

DB_IDS = (
    "financial", "formula_1", "debit_card_specializing", "california_schools",
    "thrombosis_prediction", "toxicology", "student_club", "superhero",
)
FUNCTIONS = {
    "abs", "avg", "cast", "ceil", "ceiling", "coalesce", "count", "date", "datetime",
    "current_timestamp", "current_date", "current_time", "floor", "group_concat",
    "ifnull", "iif", "instr", "julianday", "length", "like", "lower", "ltrim", "max",
    "min", "nullif", "pow", "power", "rank", "dense_rank", "row_number", "replace",
    "round", "rtrim", "strftime", "substr", "substring", "sum", "time", "total",
    "trim", "typeof", "unixepoch", "upper", "lag", "lead",
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=_json_extra)


def _json_extra(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"sqlite_blob_hex": value.hex()}
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_cases(dataset_root: str | Path) -> list[dict]:
    """Return complete corrected records for the eight selected databases.

    The pinned public input currently supplies 346 cases. Smaller local fixtures
    are supported for contract tests; no records or paraphrases are manufactured.
    """
    root = Path(dataset_root)
    source = root / ".data" / "arcwise-plat.json"
    records = json.loads(source.read_text())
    if not isinstance(records, list):
        raise ValueError("corrected annotations must be a JSON list")
    selected = [record for record in records if record.get("db_id") in DB_IDS]
    seen = set()
    for record in selected:
        for name in ("db_id", "question", "SQL"):
            if not isinstance(record.get(name), str):
                raise ValueError(f"corrected case must preserve string field {name}")
        if "evidence" not in record or not (record["evidence"] is None or isinstance(record["evidence"], str)):
            raise ValueError("corrected case must preserve evidence, including source nulls")
        if "question_id" not in record or not record["SQL"].strip():
            raise ValueError("corrected case needs question_id and source SQL")
        key = (record["db_id"], str(record["question_id"]))
        if key in seen:
            raise ValueError(f"duplicate case ID: {key}")
        seen.add(key)
    if not selected:
        raise ValueError("no cases for the selected databases")
    saved = root / "selected-cases.json"
    if saved.exists() and json.loads(saved.read_text()) != selected:
        raise ValueError("selected-cases.json differs from the complete corrected source records")
    return selected


def make_catalog(dataset_root: str | Path, db_id: str):
    """Create the new adapter using original SQLite and corrected descriptions."""
    from .database import SQLiteCatalog

    if db_id not in DB_IDS:
        raise ValueError("database is outside the selected dataset")
    data = Path(dataset_root) / ".data"
    return SQLiteCatalog(
        data / "databases" / db_id / f"{db_id}.sqlite", db_id,
        description_dir=data / "corrected-descriptions" / db_id / "database_description",
        timeout_s=3, max_rows=10000, max_result_bytes=8000000,
    )


def _value_key(value: Any) -> tuple:
    # Numeric equality is exact, without a floating-point tolerance. Keep text,
    # blobs, NULL and booleans separate; SQLite itself returns booleans as ints.
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            raise ValueError("NaN has no exact-equality comparison")
        return ("number", value)
    if isinstance(value, (str, bytes)):
        return (type(value).__name__, value)
    raise ValueError(f"non-SQLite scalar in row: {type(value).__name__}")


def _checked_rows(rows: Any) -> tuple[list[tuple], int | None]:
    if not isinstance(rows, list):
        raise ValueError("result must be a list of positional rows")
    names = None
    values = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"columns", "values"}:
            raise ValueError("each row requires exactly columns and values")
        columns, cells = row["columns"], row["values"]
        if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
            raise ValueError("columns must be a list of names, including duplicate names")
        if not isinstance(cells, list) or len(columns) != len(cells):
            raise ValueError("column count must match positional value count")
        if names is not None and columns != names:
            raise ValueError("column metadata changed between rows")
        names = columns
        values.append(tuple(_value_key(cell) for cell in cells))
    return values, None if names is None else len(names)


def compare_rows(actual: list[dict], expected: list[dict], *, ordered: bool = False) -> dict:
    """Compare values by column position, retaining row multiplicity.

    Aliases may differ between queries. Empty lists carry no cursor description,
    so their column shape cannot be assessed using this row protocol.
    """
    result = {
        "mode": "ordered" if ordered else "unordered_multiset",
        "aliases_ignored": True, "duplicate_rows_preserved": True,
        "numeric_comparison": "exact_numeric_equality_without_tolerance",
        "semantic_correctness": "not_assessed",
        "limitations": "A finite database snapshot cannot prove logical equivalence.",
    }
    try:
        a, a_width = _checked_rows(actual)
        b, b_width = _checked_rows(expected)
    except ValueError as exc:
        return dict(result, status="protocol_error", result_equal=False,
                    shape_assessed=False, message=str(exc))
    result.update(actual_rows=len(a), expected_rows=len(b), actual_columns=a_width,
                  expected_columns=b_width, shape_assessed=a_width is not None and b_width is not None)
    if not a and not b:
        return dict(result, status="empty_result_agreement", result_equal=True,
                    shape_status="shape_unassessed")
    equal = a_width == b_width and (a == b if ordered else Counter(a) == Counter(b))
    return dict(result, status="nonempty_result_agreement" if equal else "result_mismatch",
                result_equal=equal, shape_status="assessed" if result["shape_assessed"] else "shape_unassessed")


def _execute_reference(db_path: Path, sql: str) -> list[dict]:
    """Independent SQLite path: no new-adapter validation, rewriting or search.

    sqlite3.execute admits one statement; its authorizer denies all non-read
    actions and unknown functions. A progress deadline and output bounds apply.
    """
    conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    try:
        conn.enable_load_extension(False)
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        deadline = time.perf_counter() + 3

        def authorize(action, a, b, database, trigger):
            if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_RECURSIVE):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and str(b or a).lower() in FUNCTIONS:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        conn.set_authorizer(authorize)
        conn.set_progress_handler(lambda: int(time.perf_counter() > deadline), 10000)
        cursor = conn.execute(sql)
        if cursor.description is None:
            raise ValueError("reference did not produce a result set")
        columns = [description[0] for description in cursor.description]
        values = cursor.fetchmany(10001)
        if len(values) > 10000:
            raise ValueError("reference exceeded 10000 rows")
        rows = [{"columns": columns.copy(), "values": list(row)} for row in values]
        if len(_json(rows).encode()) > 8000000:
            raise ValueError("reference exceeded 8000000 result bytes")
        return rows
    finally:
        conn.close()


def _structure(sql: str, question: str) -> dict:
    tree = sqlglot.parse_one(sql, read="sqlite")
    if tree is None:
        raise ValueError("source SQL is empty")
    return {
        "joins": sum(1 for _ in tree.find_all(exp.Join)),
        "select_nodes": sum(1 for _ in tree.find_all(exp.Select)),
        "group_by_nodes": sum(1 for _ in tree.find_all(exp.Group)),
        "window_nodes": sum(1 for _ in tree.find_all(exp.Window)),
        "question_words": len(re.findall(r"\b\w+(?:[-']\w+)*\b", question)),
        "ordered": isinstance(tree.args.get("order"), exp.Order),
        "clock_dependent": any(
            node.key in {"currenttimestamp", "currentdate", "currenttime"}
            or (isinstance(node, exp.Literal) and node.is_string and node.this.lower() == "now")
            for node in tree.walk()
        ),
    }


def _error(exc: Exception) -> dict:
    return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)[:500]}


def _result_record(rows: list[dict]) -> dict:
    _, width = _checked_rows(rows)
    return {"status": "ok", "rows": len(rows), "columns": width,
            "protocol": "positional_columns_and_values",
            "raw_result_sha256": hashlib.sha256(_json(rows).encode()).hexdigest(),
            "digest_scope": "raw observed order and aliases; not a semantic equivalence key"}


async def check_dataset(dataset_root: str | Path, output_dir: str | Path) -> dict:
    """Check all selected reference cases through the adapter, with zero endpoints.

    An existing output directory is refused even when empty. Errors remain per
    case, so the complete selected sample is accounted for in the summary.
    """
    root, output = Path(dataset_root).resolve(), Path(output_dir).resolve()
    cases = load_cases(root)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = {
        "scope": "offline_adapter_contract_check",
        "model_accuracy": "not_measured", "semantic_correctness": "not_assessed",
        "endpoints_called": 0, "reference_sql_in_endpoint_payloads": False,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "versions": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                     "sqlglot": sqlglot.__version__},
        "source_hashes": {}, "database_hashes": {}, "code_hashes": {},
        "limits": {"each_query_timeout_s": 3, "max_rows": 10000, "max_result_bytes": 8000000},
        "limitations": [
            "Agreement with source SQL on this snapshot is not generated-SQL accuracy or semantic correctness.",
            "Empty results contain no column metadata: shape is unassessed even when both are empty.",
            "Floating-point values use exact numeric equality without tolerance.",
            "No-ORDER-BY queries compare multisets; ordered queries compare row sequences.",
            "Tied ORDER BY values and LIMIT without deterministic tie-breaking can vary across plans.",
            "Clock-dependent cases are flagged; runs at different times may produce different results.",
            "The SQLite progress deadline is cooperative, not an operating-system hard kill.",
        ],
    }
    for relative in (".data/arcwise-plat.json", "selected-cases.json", "download-manifest.json",
                     "corrected-descriptions-manifest.json"):
        path = root / relative
        if path.is_file():
            report["source_hashes"][relative] = _sha256(path)
    for name in ("evaluation.py", "database.py", "models.py"):
        path = Path(__file__).with_name(name)
        if path.is_file():
            report["code_hashes"][name] = _sha256(path)
    db_ids = sorted({case["db_id"] for case in cases})
    for db_id in db_ids:
        path = root / ".data" / "databases" / db_id / f"{db_id}.sqlite"
        report["database_hashes"][db_id] = _sha256(path)

    catalogs, catalog_errors, observations = {}, {}, []
    try:
        for db_id in db_ids:
            try:
                catalogs[db_id] = make_catalog(root, db_id)
            except Exception as exc:
                catalog_errors[db_id] = _error(exc)
        for case in cases:
            case_started = time.perf_counter()
            record = {"db_id": case["db_id"], "question_id": str(case["question_id"]),
                      "source_sql_sha256": hashlib.sha256(case["SQL"].encode()).hexdigest()}
            try:
                record["structure"] = dict(status="ok", **_structure(case["SQL"], case["question"]))
            except Exception as exc:
                record["structure"] = _error(exc)
            reference_start = time.perf_counter()
            expected = None
            try:
                path = root / ".data" / "databases" / case["db_id"] / f"{case['db_id']}.sqlite"
                expected = await asyncio.to_thread(_execute_reference, path, case["SQL"])
                record["reference_execution"] = _result_record(expected)
            except Exception as exc:
                record["reference_execution"] = _error(exc)
            record["reference_execution"]["elapsed_ms"] = round((time.perf_counter() - reference_start) * 1000, 3)
            actual = None
            validation_start = time.perf_counter()
            query = None
            try:
                if case["db_id"] in catalog_errors:
                    raise ValueError("catalog initialization failed: " + catalog_errors[case["db_id"]]["message"])
                query = catalogs[case["db_id"]].validate(case["SQL"])
                record["validation"] = {
                    "status": "ok", "schema_id": query.schema_id,
                    "validated_sql_sha256": hashlib.sha256(query.sql.encode()).hexdigest(),
                }
            except Exception as exc:
                record["validation"] = _error(exc)
            record["validation"]["elapsed_ms"] = round((time.perf_counter() - validation_start) * 1000, 3)
            if query is not None:
                adapter_start = time.perf_counter()
                try:
                    actual = await catalogs[case["db_id"]].search(query)
                    record["adapter_execution"] = _result_record(actual)
                except Exception as exc:
                    record["adapter_execution"] = _error(exc)
                record["adapter_execution"]["elapsed_ms"] = round((time.perf_counter() - adapter_start) * 1000, 3)
            else:
                record["adapter_execution"] = {"status": "not_run", "reason": "validation_failed", "elapsed_ms": 0}
            if (expected is not None and actual is not None
                    and record["reference_execution"]["status"] == "ok"
                    and record["adapter_execution"]["status"] == "ok"):
                comparison_start = time.perf_counter()
                record["comparison"] = compare_rows(actual, expected, ordered=record["structure"].get("ordered", False))
                record["comparison"]["elapsed_ms"] = round((time.perf_counter() - comparison_start) * 1000, 3)
                record["status"] = record["comparison"]["status"]
            else:
                record["comparison"] = {"status": "not_assessed", "semantic_correctness": "not_assessed"}
                record["status"] = "execution_or_validation_error"
            record["elapsed_ms"] = round((time.perf_counter() - case_started) * 1000, 3)
            observations.append(record)
            print(_json({key: record[key] for key in ("db_id", "question_id", "status", "elapsed_ms")}), flush=True)
    finally:
        for catalog in catalogs.values():
            await catalog.close()

    def summarize(records: list[dict]) -> dict:
        return {
            "cases": len(records), "statuses": dict(Counter(record["status"] for record in records)),
            "validation_ok": sum(record["validation"]["status"] == "ok" for record in records),
            "adapter_execution_ok": sum(record["adapter_execution"]["status"] == "ok" for record in records),
            "reference_execution_ok": sum(record["reference_execution"]["status"] == "ok" for record in records),
            "join_cases": sum(record["structure"].get("joins", 0) > 0 for record in records),
            "short_question_cases_at_most_10_words": sum(record["structure"].get("question_words", 10000) <= 10 for record in records),
            "short_question_join_cases": sum(record["structure"].get("question_words", 10000) <= 10 and record["structure"].get("joins", 0) > 0 for record in records),
            "clock_dependent_cases": sum(record["structure"].get("clock_dependent", False) for record in records),
        }

    report.update(summarize(observations))
    report["per_database"] = {db_id: summarize([record for record in observations if record["db_id"] == db_id]) for db_id in db_ids}
    report["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "cases.json").write_text(_json(observations) + "\n")
    (output / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report
