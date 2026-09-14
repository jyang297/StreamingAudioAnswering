---
ai_contribution: authored
date: 2026-09-13
---

# v6 local verification

**74 local tests passed. All 346 corrected BIRD reference queries passed v6 validation and execution, with matching results from an independent read-only SQLite connection.** No LLM endpoint was called in these checks.

| Check | Observed result | Evidence boundary |
|---|---|---|
| New v6 tests | 74 passed | Contract, endpoint transport with mocks, real small SQLite fixtures, scheduling, cancellation and scoring regressions. |
| Real public databases | 346 validated; 346 executed; 346 nonempty result agreements | Tests the adapter against original source SQL on this data snapshot; not generated-query accuracy. |
| Dataset structure | 284 JOIN cases; 65 questions with ≤10 words, 47 of those include JOIN | Eight separate databases; does not cover genuine one- or two-word conversational followups. |
| Existing checkpoint | v5 unchanged | Reused scheduler contract; no new production/SDK/audio claim. |

Final public-data evidence is in [adapter-346-20260913-3/summary.json](evidence/adapter-346-20260913-3/summary.json) and [per-case results](evidence/adapter-346-20260913-3/cases.json). It records source/database/code hashes and Python 3.12.14, SQLite 3.53.1, SQLGlot 27.29.0. The run took about 8.99 seconds for the entire offline verification job; that is not voice-assistant response latency. Eleven queries have current-time dependencies and remain flagged.

The first run, [adapter-346-20260913](evidence/adapter-346-20260913/summary.json), retained a 345/346 validation result. A CTE with COUNT(*) triggered an unusual empty-column authorization callback. A narrow scope fix resolved it. The second passing report remains historical because a later quoted-identifier fix changed the adapter. The `-3` report matches the final core code hashes.

Independent review also found two issues outside SQL execution: fractional negative transcript timestamps could be accepted, and successful answer-time rewriting could incorrectly improve the recorded initial retrieval outcome. Both now have regression tests. Initial retrieval evidence and answer-time evidence are scored separately, so a repaired wrong reuse remains a wrong reuse in the initial retrieval metrics.

SQLite's double-quoted-string compatibility behavior was disabled. Without that change, `SELECT "misspelled_column" ...` could succeed as a constant string. Unknown quoted columns now fail, valid quoted columns with spaces work, and environments without the required DQS setting fail explicitly.

Commands used for local verification:

```sh
python -m pytest -q
python -m multitable_poc.run check-data --out evidence/adapter-new-run
```

Canonical-path installation/import and configured integration checks also passed; see [local verification](evidence/local-verification-20260913.json).

The final public-data check invoked the same `check_dataset` coroutine directly; the CLI delegates to it. Historical v5 dependency files were incomplete, so the tests used a new isolated temporary v6 environment. Pinned package versions are in `requirements.txt`; v5's environment was not modified.

Model-generated SQL quality, semantic cache precision/latency, actual Vertex transport, Cloud SQL parity and LiveKit speech timing remain unmeasured. Scripted endpoint tests verify wiring and rejection behavior only. SQL result agreement does not score natural-language answer correctness.
