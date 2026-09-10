#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker exec -i livekit-rag-postgres-fixture psql -X -v ON_ERROR_STOP=1 -U "${POSTGRES_FIXTURE_USER:-rag_reader}" -d "${POSTGRES_FIXTURE_DB:-rag_fixture}" < query.sql
