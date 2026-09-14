# Specification: multi-table SQL
Package: `multi-table-sql`
Revision: `1`
Status: `active`
Profile: `development`

## Requirements
| ID | Status | Statement | Supersedes |
|---|---|---|---|
| REQ-001 | active | Compile and execute scoped read-only multi-table SQLite queries without changing their meaning. | - |
| REQ-002 | active | Bind generic Builder/Checker/Answerer to actual schema; retain final-builder independence and per-step timing. | - |
| REQ-003 | active | Evaluate real BIRD data with gold isolated from online payloads and honest finite-result scoring. | - |

## Acceptance criteria
| ID | Requirement | Status | Behavior |
|---|---|---|---|
| AC-001 | REQ-001 | active | JOIN, aliases, CTEs, nested SELECT and dataset expressions work; unknown/ambiguous/write/cross-scope queries fail. |
| AC-002 | REQ-001 | active | Preserve SQL and duplicate output columns; bounds/cancellation never silently yield partial answers. |
| AC-003 | REQ-002 | active | Complete selected schema descriptions reach Builder; Checker excludes other db/schema; model output cannot choose routing. |
| AC-004 | REQ-002 | active | Configurable complex-SQL output budget and request cap; trace Builder, validation, Checker, DB and total times. |
| AC-005 | REQ-003 | active | All 346 references traverse v6 and compare to independent original-SQL execution; duplicates/order/empty shape handled explicitly. |
| AC-006 | REQ-003 | active | Final-only and scripted speculative runners share schema/evidence policies; oracle wiring tests do not count as model accuracy. |

## Test cases
| ID | Acceptance | Status | Test location |
|---|---|---|---|
| TEST-001 | AC-001, AC-002 | passed | tests/test_database.py |
| TEST-002 | AC-003, AC-004 | passed | tests/test_endpoints.py |
| TEST-003 | AC-005 | passed | tests/test_evaluation.py; real-data report |
| TEST-004 | AC-006 | passed | tests/test_pipeline.py; tests/test_run.py |

## Invariants and non-goals
One selected database per request; read-only file and SQL authorizer are mandatory. Schema fingerprint is not data freshness. No audio cache, Chroma population, SQL acceleration, production migration or Vertex accuracy claim. Scripted timings are not voice measurements.

## Change history
| Change | Status | Summary | Approval |
|---|---|---|---|
| CHANGE-001 | applied | Separate local multi-table extension. | User: 需要拓展 因为工作环境也是复杂多表; reversible details in linked brief. |
