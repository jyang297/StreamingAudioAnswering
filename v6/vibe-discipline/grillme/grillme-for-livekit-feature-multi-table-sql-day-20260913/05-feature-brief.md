# Feature brief: v6 multi-table SQL
Status: READY WITH ASSUMPTIONS
Outcome: use real multi-table BIRD databases through the same query contract used by Builder, Checker, execution and evaluation.
Acceptance: 346 source SELECTs compile and execute through v6; JOIN/aliases/CTEs/subqueries/aggregation/windows supported as present in data; schema scope enforced; writes/unknown tables and columns/ambiguous names rejected; no implicit LIMIT; duplicate output columns retained; row/time/cancellation limits enforced; logs include per-step elapsed_ms; gold never enters online payloads.
Design: immutable schema metadata from actual SQLite; Query(sql, db_id, schema_id); catalog validates and asynchronously executes; generic endpoint classes use schema descriptions; existing ordered-turn policy reused. Checker filters scope before any LLM selection. Endpoint output budget increased/configurable for complex SQL.
Non-goals: audio caching, SQL acceleration, Chroma population, generated paraphrase labels, Cloud SQL migration, actual Vertex authentication, semantic correctness proof, production latency claims.
Delivery: CHARACTERIZATION/SPIKE for adapting the public dataset; meaningful negative tests and integration checks. Refactor judgment after implementation. Evidence must label scripted/oracle endpoints explicitly.
Workflow handoff: this record; ../../learning/learning-for-livekit-feature-multi-table-sql-day-20260913; next spec-driven-delivery, then explain-what-we-built. Learning unassessed.
