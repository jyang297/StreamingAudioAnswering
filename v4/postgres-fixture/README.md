# Local PostgreSQL retrieval fixture

This disposable fixture uses container `livekit-rag-postgres-fixture`, named volume `livekit-rag-postgres-fixture-data`, and loopback address `127.0.0.1:55432`. It has one table, `northwind_products`, with product name, category/supplier IDs, price, stock, ordering and discontinued fields.

Source: [Northwind products.csv at commit `8677f359`](https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/8677f359f35a70d4a52c42b07cc30931ba78208f/examples/northwind/data/csv/products.csv), from the graphql-compose examples repository, containing the standard Northwind sample products. The pinned bytes have SHA-256 `bc377ab1fac01d6e99cb659d30d4bce10d77c23d8c97242c2dd5e649d2f5a4ea` and 77 data rows. The repository API did not expose a license file, so this fixture makes no redistribution license claim; check upstream licensing before redistribution.

Run `./setup.sh` then `./query.sh`. `import.sh` verifies the pinned checksum before import and recreates the one table deterministically. Connection details: host `127.0.0.1`, port `55432`, database `rag_fixture`, user `rag_reader`; the generated password is kept in ignored `.env`.

This proves ordinary SQL filtering/text retrieval only; it is not a cloud latency, semantic relevance, embedding, LLM, or production durability proof.

`query.sql` is a fixed smoke-query script, not a dynamic parameterized API. The
v4 Python `PostgresCatalog` adapter supplies true bound parameters and read-only
transactions. The bootstrap user `rag_reader` is the image's database owner
(despite its name), not a least-privilege production role. DDL and COPY now run
in one transaction. Raw CSV and credentials remain ignored and are not committed.
