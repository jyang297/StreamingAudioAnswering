from __future__ import annotations

import os
import asyncio
import logging
import time
from pathlib import Path

import asyncpg

from .models import Query


def fixture_password(path):
    """Read only this task's generated credential internally, never shell-source it."""
    for line in Path(path).read_text().splitlines():
        if line.startswith("POSTGRES_FIXTURE_PASSWORD="):
            return line.partition("=")[2].strip()
    raise ValueError("fixture password missing")


class PostgresCatalog:
    def __init__(self, pool):
        self.pool = pool
        self.metrics = []

    @classmethod
    async def connect(cls, *, credential_file=None):
        password = (fixture_password(credential_file) if credential_file else
                    os.environ.get("RAG_DB_PASSWORD"))
        pool = await asyncpg.create_pool(host=os.environ.get("RAG_DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("RAG_DB_PORT", "55432")),
            database=os.environ.get("RAG_DB_NAME", "rag_fixture"),
            user=os.environ.get("RAG_DB_USER", "rag_reader"), password=password,
            min_size=1, max_size=3, timeout=5, command_timeout=3)
        return cls(pool)

    async def search(self, query: Query):
        # Query is validated again even when an adapter constructs it directly.
        query = Query.parse(query.json())
        order = {"product_id": "product_id", "price_asc": "unit_price ASC, product_id",
                 "price_desc": "unit_price DESC, product_id"}[query.order]
        sql = """SELECT product_id, product_name, category_id, quantity_per_unit,
                        unit_price::float8 AS unit_price, units_in_stock, discontinued
                 FROM northwind_products
                 WHERE ($1::text IS NULL OR strpos(lower(product_name), lower($1)) > 0)
                   AND ($2::int IS NULL OR category_id = $2)
                   AND ($3::float8 IS NULL OR unit_price >= $3)
                   AND ($4::float8 IS NULL OR unit_price <= $4)
                   AND ($5::boolean IS NULL OR (units_in_stock > 0) = $5)
                   AND ($6::boolean IS NULL OR discontinued = $6)
                 ORDER BY """ + order + " LIMIT $7"
        started = time.perf_counter()
        entry = {"query": query.json(), "status": "error"}
        self.metrics.append(entry)
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction(readonly=True):
                    rows = await conn.fetch(sql, query.name, query.category_id, query.min_price,
                        query.max_price, query.in_stock, query.discontinued, query.limit)
            result = [dict(row) for row in rows]
            entry.update(status="ok", rows=len(result))
            return result
        finally:
            entry["elapsed_ms"] = (time.perf_counter() - started) * 1000

    async def close(self):
        try:
            await asyncio.wait_for(self.pool.close(), timeout=5)
        except TimeoutError:
            self.pool.terminate()
            logging.getLogger(__name__).warning("PostgreSQL graceful close timed out; pool terminated")
