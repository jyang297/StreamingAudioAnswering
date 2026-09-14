# v7 partial experiment handoff

- Design authority: ../README.md and ../../v6/BUILDER-DIRECTIONS.md; user selected lightweight Builder and authorized real partial replay. Scope is READY WITH ASSUMPTIONS: synthetic text timing, public-only fixtures, no semantic hit labels.
- Reused upstream: ../../v6/vibe-discipline/index.md. Reopened only the Builder branch; do not overwrite its SQL-adapter evidence. This index uses paths relative to v7-partial unless linked otherwise.
- REQ-P1: no schema/SQL/future text in Builder. Evidence: replay.py payload allowlist, test_contract.py test_no_future_or_gold_in_early_payload, recorded online payloads.
- REQ-P2: real embeddings and same-DB scope. Evidence: replay.py encode/search and runtime-lock.txt; observed 200-vector load and per-query inference. No hash similarity fallback.
- REQ-P3: bounded live endpoint calls and per-step time. Evidence: frozen manifest, 72 recorded calls, summary and timing.jsonl. No retries or follow-on generation.
- REQ-P4: no automatic answer adoption. Evidence: runner only retrieves and logs; no Answerer or SQL executor imported.
- Process: CHARACTERIZATION/SPIKE, three boundary tests passed before live run. No claimed TDD RED. Refactor judgment SKIP: first isolated experiment; no product refactor needed.
- Implementation: experiment LOCAL VERIFIED, outcome limits in ../RESULTS.md. Production integration UNVERIFIED. Learning: unassessed, agent-run demonstration; no independent mastery inference.
- Current findings: wait calls dominate, final exact replays show no retrieval improvement, stable candidate/rising score can preserve a mismatch. These are observations, not a trained scheduling policy.
- Next recommended skill: explain-what-we-built for this bounded experiment if a code walkthrough is requested; otherwise discuss the evidence before further calls. LiveKit preemption remains mandatory and pending.

- Successor scope approved: [length-gated long/compound replay](../GATED-DESIGN.md), three-word experimental gate with final bypass, separate runner and evidence; original replay retained.

- Length-gated replay complete: [results](../GATED-RESULTS.md), 128 injections / 36 local skips / 92 real calls, no HTTP/contract errors. Six boundary tests passed. Proposed per-subquestion readiness is NOT implemented; next decision is compound query representation.

- 2026-09-14 handoff: [current experiment summary](../HANDOFF.md). Priority updated: real baseline/preemptive timing before additional Builder complexity; prompt optimization and subquestion contracts remain unimplemented. No new LLM run or push.
