#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
CONTAINER_NAME="livekit-rag-postgres-fixture"
VOLUME_NAME="livekit-rag-postgres-fixture-data"
HOST_PORT="${POSTGRES_FIXTURE_PORT:-55432}"
DB_NAME="${POSTGRES_FIXTURE_DB:-rag_fixture}"
DB_USER="${POSTGRES_FIXTURE_USER:-rag_reader}"
if [[ ! -f .env ]]; then
  DB_PASSWORD="$(openssl rand -hex 20)"; umask 077
  printf 'POSTGRES_FIXTURE_PASSWORD=%s\n' "$DB_PASSWORD" > .env
else
  DB_PASSWORD="$(sed -n 's/^POSTGRES_FIXTURE_PASSWORD=//p' .env)"
fi
[[ -n "$DB_PASSWORD" ]] || { echo 'Missing password in .env' >&2; exit 1; }
docker volume create "$VOLUME_NAME" >/dev/null
if ! docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  docker run -d --name "$CONTAINER_NAME" -e POSTGRES_DB="$DB_NAME" -e POSTGRES_USER="$DB_USER" -e POSTGRES_PASSWORD="$DB_PASSWORD" -p "127.0.0.1:${HOST_PORT}:5432" -v "$VOLUME_NAME:/var/lib/postgresql/data" postgres:16-alpine >/dev/null
else
  [[ "$(docker inspect -f '{{.Config.Image}}' "$CONTAINER_NAME")" == "postgres:16-alpine" ]] || { echo "Existing fixture container has unexpected image" >&2; exit 1; }
  docker start "$CONTAINER_NAME" >/dev/null || true
fi
for _ in $(seq 1 30); do
  docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1 && break
  sleep 1
done
docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME"
./import.sh
