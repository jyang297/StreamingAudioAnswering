"""Offline multi-table checks or explicitly configured endpoint experiments."""
from __future__ import annotations

import argparse
import asyncio
import copy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
import statistics
import time

from .compat import POC_ROOT, span
from .endpoints import Builder, Checker, Answerer, JSONEndpoint, prompt_hashes
from .evaluation import check_dataset, load_cases, make_catalog, compare_rows, _execute_reference, _structure
from .pipeline import MultiTablePipeline


def case_id(case):
    return case["db_id"] + ":" + str(case["question_id"])


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def validate_schedule(schedule):
    if not isinstance(schedule, dict) or set(schedule) != {"source_label", "final_at_ms", "snapshots"}:
        raise ValueError("schedule requires source_label, final_at_ms and snapshots")
    if not isinstance(schedule["source_label"], str) or not schedule["source_label"].strip():
        raise ValueError("schedule must describe its source; no inferred speech timing")
    final_at = schedule["final_at_ms"]
    if type(final_at) not in (int, float) or not math.isfinite(final_at) or not 0 <= final_at <= 60000:
        raise ValueError("final_at_ms must be finite and within 0..60000")
    snapshots = schedule["snapshots"]
    if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 200:
        raise ValueError("schedule needs 1..200 cumulative snapshots")
    previous = 0
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or set(snapshot) != {"at_ms", "text"}:
            raise ValueError("snapshot requires at_ms and text only")
        at = snapshot["at_ms"]
        if type(at) not in (int, float) or not math.isfinite(at) or not previous <= at <= final_at:
            raise ValueError("snapshot times must be ordered and precede final")
        if not isinstance(snapshot["text"], str) or not snapshot["text"].strip():
            raise ValueError("snapshot text must be nonempty")
        previous = at
    return schedule


async def run_case(case, arm, endpoint, catalog, *, schedule=None, evidence_policy="none",
                   answer=False, min_interval_ms=150, change_threshold=3, trigger_policy="hybrid",
                   max_partials=2):
    if arm not in {"final-only", "speculative"} or evidence_policy not in {"none", "provided"}:
        raise ValueError("unsupported arm or evidence policy")
    if arm == "speculative":
        validate_schedule(schedule)
    builder = Builder(endpoint, catalog,
        benchmark_evidence=case.get("evidence") if evidence_policy == "provided" else None)
    pipeline = MultiTablePipeline(builder, Checker(endpoint, catalog), catalog, Answerer(endpoint, catalog),
        speculate=arm == "speculative", trigger_policy=trigger_policy,
        min_interval=min_interval_ms / 1000, change_threshold=change_threshold,
        max_builder_calls=max_partials, max_candidates=2, final_timeout=60, answer_timeout=60)
    http_start, db_start = len(endpoint.metrics), len(catalog.metrics)
    pipeline.start_turn([])  # BIRD single-turn cases contain no confirmed history.
    origin = time.perf_counter()
    try:
        if arm == "speculative":
            for snapshot in schedule["snapshots"]:
                await asyncio.sleep(max(0, origin + snapshot["at_ms"] / 1000 - time.perf_counter()))
                pipeline.observe(snapshot["text"])
            await asyncio.sleep(max(0, origin + schedule["final_at_ms"] / 1000 - time.perf_counter()))
        final_start = time.perf_counter()
        with span("final_to_retrieval", sink=pipeline.timings, case_id=case_id(case), arm=arm):
            bundle = await pipeline.finish(case["question"])
        retrieval_ms = (time.perf_counter() - final_start) * 1000
        # Match the evidence being scored to the time being measured. A later
        # Answerer repair must not turn wrong initial reuse into a fast success.
        evidence = copy.deepcopy(bundle.evidence[-1]) if bundle.evidence else None
        if answer:
            with span("final_to_answer_remaining", sink=pipeline.timings, case_id=case_id(case), arm=arm):
                await pipeline.answer(bundle)
        total_ms = (time.perf_counter() - final_start) * 1000
        record = {"case_id": case_id(case), "arm": arm, "schema_id": catalog.schema_id,
                  "evidence_policy": evidence_policy, "schedule_source": schedule["source_label"] if arm == "speculative" else None,
                  "path": bundle.path, "final_query": pipeline.last_final_query.json() if pipeline.last_final_query else None,
                  "builder_calls": builder.records, "post_final_retrieval_ms": retrieval_ms,
                  "post_final_answer_ms": total_ms if answer else None,
                  "answer_text": bundle.answer, "rewrites": bundle.rewrites}
        answer_evidence = bundle.evidence[-1] if answer and bundle.evidence else None
    finally:
        pending = await pipeline.close(timeout=4)
        if pending:
            raise RuntimeError("pipeline tasks did not drain")
    # Freeze online costs before gold is executed. Gold is only available here.
    record.update(http_calls=endpoint.metrics[http_start:], database_calls=catalog.metrics[db_start:],
                  timings=pipeline.timings, trace=pipeline.trace)
    try:
        with span("offline_reference_execution", case_id=case_id(case)):
            expected = await asyncio.to_thread(_execute_reference, catalog.db_path, case["SQL"])
        structure = _structure(case["SQL"], case["question"])
        record["structure"] = structure
        if evidence is None or evidence.error:
            record["comparison"] = {"status": "no_valid_result", "result_equal": False,
                                    "error": evidence.error if evidence else None}
        else:
            record["comparison"] = compare_rows(evidence.rows, expected, ordered=structure["ordered"])
            record["returned_query"] = evidence.query.json()
        record["outcome"] = record["comparison"]["status"]
        if answer:
            if answer_evidence is None or answer_evidence.error:
                record["answer_evidence_comparison"] = {"status": "no_valid_result", "result_equal": False}
            else:
                record["answer_evidence_comparison"] = compare_rows(answer_evidence.rows, expected, ordered=structure["ordered"])
                record["answer_evidence_query"] = answer_evidence.query.json()
            record["answer_text_correctness"] = "not_assessed"
    except Exception as exc:
        record.update(outcome="reference_unavailable", reference_error=type(exc).__name__)
    # Finite reference disagreement after reuse is an observed failure, not an
    # exhaustive false-positive measurement. Empty shape remains unassessed.
    record["reuse_reference_disagreement"] = bundle.path.startswith("reuse_") and record["outcome"] == "result_mismatch"
    record["semantic_correctness"] = "not_assessed"
    return record


def summarize(records):
    arms = {}
    for arm in sorted({record["arm"] for record in records}):
        rows = [r for r in records if r["arm"] == arm]
        times = sorted(r["post_final_retrieval_ms"] for r in rows)
        arms[arm] = {"cases": len(rows), "outcomes": dict(Counter(r["outcome"] for r in rows)),
                     "paths": dict(Counter(r["path"] for r in rows)),
                     "http_calls": sum(len(r["http_calls"]) for r in rows),
                     "observed_reuse_reference_disagreements": sum(r["reuse_reference_disagreement"] for r in rows),
                     "all_post_final_retrieval_ms": {"p50": statistics.median(times),
                         "p95": times[max(0, math.ceil(.95 * len(times)) - 1)]}}
    baseline = {r["case_id"]: r for r in records if r["arm"] == "final-only"}
    paired = []
    for row in records:
        other = baseline.get(row["case_id"])
        if row["arm"] == "speculative" and other and row["outcome"] == other["outcome"] == "nonempty_result_agreement":
            paired.append({"case_id": row["case_id"], "saved_ms": other["post_final_retrieval_ms"] - row["post_final_retrieval_ms"]})
    return {"scope": "finite reference result comparison; no semantic equivalence or voice-latency proof",
            "arms": arms, "paired_nonempty_agreement": paired,
            "paired_saved_ms_median": statistics.median(r["saved_ms"] for r in paired) if paired else None}


async def evaluate(args):
    cases = load_cases(args.dataset_root)
    if args.case_ids:
        wanted = set(args.case_ids)
        cases = [c for c in cases if case_id(c) in wanted]
        if {case_id(c) for c in cases} != wanted:
            raise ValueError("unknown case IDs; use db_id:question_id")
    if args.limit is not None:
        cases = cases[:args.limit]
    schedules = json.loads(Path(args.schedules).read_text()) if args.schedules else {}
    if "speculative" in args.arms:
        for case in cases:
            validate_schedule(schedules.get(case_id(case)))
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    endpoint, catalogs, records = None, {}, []
    status = {"complete": False, "requested_runs": len(cases) * len(args.arms), "runs": 0}
    try:
        for db_id in {c["db_id"] for c in cases}:
            catalogs[db_id] = make_catalog(args.dataset_root, db_id)
        endpoint = JSONEndpoint.from_env(env_file=args.env_file, max_calls=args.max_calls)
        dump(output / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
            "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
            "case_ids": [case_id(c) for c in cases], "arms": args.arms, "model": endpoint.model,
            "prompt_hashes": prompt_hashes(), "schema_ids": {k: v.schema_id for k, v in catalogs.items()},
            "evidence_policy": args.evidence_policy, "schedules": schedules,
            "output_tokens": endpoint.output_tokens, "max_http_calls": args.max_calls,
            "scheduler": {"trigger_policy": args.trigger_policy, "min_interval_ms": args.min_interval_ms,
                "change_threshold": args.change_threshold, "max_partials": args.max_partials},
            "measurement": "SQL result readiness after final text, optional answer completion; no audio",
            "order": "rotate arm order by case", "qa_cache": "not populated"})
        for index, case in enumerate(cases):
            ordered_arms = args.arms[index % len(args.arms):] + args.arms[:index % len(args.arms)]
            for arm in ordered_arms:
                worst_case = 1 + (args.max_partials + 1 if arm == "speculative" else 0) + (2 if args.answer else 0)
                if len(endpoint.metrics) + worst_case > args.max_calls:
                    status["reason"] = "insufficient_remaining_call_budget"
                    return summarize(records)
                record = await run_case(case, arm, endpoint, catalogs[case["db_id"]],
                    schedule=schedules.get(case_id(case)), evidence_policy=args.evidence_policy,
                    answer=args.answer, trigger_policy=args.trigger_policy, min_interval_ms=args.min_interval_ms,
                    change_threshold=args.change_threshold, max_partials=args.max_partials)
                records.append(record)
                with (output / "results.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(json.dumps({k: record[k] for k in ("case_id", "arm", "outcome", "post_final_retrieval_ms")}), flush=True)
                dump(output / "summary.json", summarize(records))
        status["complete"] = True
        return summarize(records)
    except Exception as exc:
        status["error_type"] = type(exc).__name__
        raise
    finally:
        status["runs"] = len(records)
        dump(output / "status.json", status)
        dump(output / "summary.json", summarize(records))
        if endpoint is not None:
            dump(output / "http-metrics.json", endpoint.metrics)
            await endpoint.close()
        for catalog in catalogs.values():
            await catalog.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check-data", "evaluate"])
    parser.add_argument("--dataset-root", type=Path, default=POC_ROOT / "complex-data")
    parser.add_argument("--out", required=True)
    parser.add_argument("--env-file")
    parser.add_argument("--case-ids", nargs="+")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--arms", nargs="+", choices=["final-only", "speculative"], default=["final-only"])
    parser.add_argument("--schedules")
    parser.add_argument("--evidence-policy", choices=["none", "provided"], default="none")
    parser.add_argument("--max-calls", type=int, default=100)
    parser.add_argument("--max-partials", type=int, default=2)
    parser.add_argument("--trigger-policy", choices=["time", "text", "hybrid"], default="hybrid")
    parser.add_argument("--min-interval-ms", type=float, default=150)
    parser.add_argument("--change-threshold", type=int, default=3)
    parser.add_argument("--answer", action="store_true")
    args = parser.parse_args()
    if (args.limit is not None and args.limit < 1) or min(args.max_calls, args.max_partials, args.change_threshold) < 1:
        parser.error("counts must be positive")
    if not math.isfinite(args.min_interval_ms) or args.min_interval_ms < 0 or len(set(args.arms)) != len(args.arms):
        parser.error("invalid trigger interval or duplicate arms")
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger("rag_poc.timing").setLevel(logging.INFO)
    if args.mode == "check-data":
        result = asyncio.run(check_dataset(args.dataset_root, args.out))
        print(json.dumps({k: v for k, v in result.items() if k in {"cases", "statuses", "validation_ok", "adapter_execution_ok"}}, indent=2))
        if result["adapter_execution_ok"] != result["cases"] or any(
                k not in {"nonempty_result_agreement", "empty_result_agreement"} for k in result["statuses"]):
            raise SystemExit(1)
    else:
        asyncio.run(evaluate(args))
        if not json.loads((Path(args.out) / "status.json").read_text())["complete"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
