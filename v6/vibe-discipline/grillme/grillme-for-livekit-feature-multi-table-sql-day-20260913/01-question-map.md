# Branch map
Working model: schema-bound builder -> validated read-only SQL -> bounded real SQLite execution. Final builder and checker keep their separate responsibilities; scope validation is local and mandatory.
Branches in order: (1) schema and query identity; (2) read-only compilation and execution; (3) generic Builder/Checker/Answerer; (4) gold isolation and result comparison; (5) integration and portability documentation.
Dependencies: endpoint parsing uses catalog validation; evaluation uses the same adapter as generated SQL. Production latency and actual cache labels remain parked.
Stopping criterion: all 346 source queries traverse the new adapter without silently changing SQL semantics; reject write/unknown/cross-scope SQL; preserve output shape; verify scheduler flow and report finite dataset agreement separately from semantics.
Five compass areas are already answered by the preceding conversation; no duplicate interview. Reversible choices below are agent assumptions, not newly claimed user answers.
