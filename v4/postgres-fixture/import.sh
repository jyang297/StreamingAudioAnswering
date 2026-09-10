#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
CONTAINER_NAME="livekit-rag-postgres-fixture"; DB_NAME="${POSTGRES_FIXTURE_DB:-rag_fixture}"; DB_USER="${POSTGRES_FIXTURE_USER:-rag_reader}"
SOURCE_URL="https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/8677f359f35a70d4a52c42b07cc30931ba78208f/examples/northwind/data/csv/products.csv"
SOURCE_SHA256="bc377ab1fac01d6e99cb659d30d4bce10d77c23d8c97242c2dd5e649d2f5a4ea"
mkdir -p source; curl --fail --location --silent --show-error "$SOURCE_URL" -o source/products.csv
echo "$SOURCE_SHA256  source/products.csv" | shasum -a 256 -c - >/dev/null
# Official image's local Unix socket: no password passed through process argv.
# DDL and COPY share one transaction; import failure preserves the previous table.
{
  cat schema.sql
  printf '%s\n' 'COPY northwind_products FROM STDIN WITH (FORMAT csv, HEADER true);'
  cat source/products.csv
  printf '%s\n' '\.'
} | docker exec -i "$CONTAINER_NAME" psql -X --single-transaction -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME"
docker exec "$CONTAINER_NAME" psql -X -A -t -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -c 'SELECT count(*) FROM northwind_products;'
