# Evidence brief
Observed: v5/sql_poc/models.py canonical_sql permits one fixed PostgreSQL table and LIMIT 1..20; its pipeline.py mostly uses the generic query.json/search contracts. v5 endpoints and grounding hard-code Northwind products. v5 database.py converts records to dictionaries, unsuitable for duplicate JOIN output names.
Observed: ../complex-data/inventory.json describes 346 corrected BIRD cases across 8 real SQLite databases, 54 tables and 413 columns; all source SQLs executed in a separate sanity harness.
User decision: extend to complex multi-table workloads because the work environment also uses complex databases. Preserve earlier checkpoints. SQL execution is not the performance target. No audio caching or Jetson. False acceptance matters more than false rejection.
Inferred implementation scope: a new SQLite-backed v6 adapter and evaluation harness, retaining the existing ordered-turn scheduler. This is not a Cloud SQL/Vertex production integration.
Unknown: company's exact dialect/schema, authenticated Vertex transport, real partial STT timelines, cache payload and semantic hit labels. These do not block the public-data adapter.
