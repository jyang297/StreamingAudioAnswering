"""Bounded, genuinely read-only SQLite execution for public multi-table fixtures."""
from __future__ import annotations

import asyncio
import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sqlite3
import threading
import time

import sqlglot
from sqlglot import exp

from .models import ContractError, Query

MAX_SQL_CHARS = 16_000
MAX_AST_NODES = 2048
MAX_AST_DEPTH = 64
FUNCTIONS = frozenset({
    "abs", "avg", "cast", "ceil", "ceiling", "coalesce", "count", "date", "datetime",
    "current_timestamp", "current_date", "current_time", "floor", "group_concat",
    "ifnull", "iif", "instr", "julianday", "length", "like", "lower", "ltrim", "max",
    "min", "nullif", "pow", "power", "rank", "dense_rank", "row_number", "replace",
    "round", "rtrim", "strftime", "substr", "substring", "sum", "time", "total",
    "trim", "typeof", "unixepoch", "upper", "lag", "lead",
})
_FORBIDDEN = frozenset({
    "insert", "update", "delete", "create", "drop", "alter", "merge", "command",
    "attach", "detach", "pragma", "transaction", "commit", "rollback", "copy",
    "grant", "revoke", "use", "into", "lock", "execute", "loaddata", "truncate",
    "truncatetable", "placeholder", "parameter",
})


def _quoted(name):
    return '"' + name.replace('"', '""') + '"'


def _check_sql(sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql) > MAX_SQL_CHARS or "\x00" in sql:
        raise ContractError("SQL must be a nonempty string of at most 16000 characters without NUL")
    try:
        statements = sqlglot.parse(sql, read="sqlite", error_level=sqlglot.ErrorLevel.RAISE)
    except (sqlglot.errors.SqlglotError, RecursionError, ValueError) as exc:
        raise ContractError("SQL could not be parsed as SQLite") from exc
    if len(statements) != 1 or type(statements[0]) not in (exp.Select, exp.Union, exp.Intersect, exp.Except):
        raise ContractError("exactly one SELECT or set query is required")
    count = 0
    for node in statements[0].walk():
        count += 1
        if count > MAX_AST_NODES:
            raise ContractError("SQL AST is too large")
        if node.key in _FORBIDDEN:
            raise ContractError("SQL contains a forbidden statement or parameter")
        depth, parent = 0, node.parent
        while parent is not None:
            depth += 1
            if depth > MAX_AST_DEPTH:
                raise ContractError("SQL AST is too deep")
            parent = parent.parent
        if isinstance(node, (exp.Table, exp.Column)):
            if node.catalog or node.db not in ("", "main"):
                raise ContractError("cross-database references are forbidden")
    # Deliberately do not render or optimize this tree: execute the original SQL.
    return statements[0]


class _QueryCancelled(Exception):
    pass


class _Control:
    def __init__(self):
        self.cancelled = threading.Event()
        self.lock = threading.Lock()
        self.connection = None

    def cancel(self):
        self.cancelled.set()
        with self.lock:
            if self.connection is not None:
                self.connection.interrupt()


class SQLiteCatalog:
    def __init__(self, db_path, db_id, *, description_dir=None, timeout_s=3.0,
                 max_rows=10000, max_result_bytes=8000000):
        if not isinstance(db_id, str) or not db_id.strip():
            raise ContractError("a database identity is required")
        if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ContractError("timeout must be positive and finite")
        if any(type(value) is not int or value < 1 for value in (max_rows, max_result_bytes)):
            raise ContractError("result bounds must be positive integers")
        self.db_path = Path(db_path).resolve(strict=True)
        if not self.db_path.is_file():
            raise ContractError("database path must be a regular file")
        self.db_id, self.timeout_s = db_id, float(timeout_s)
        self.max_rows, self.max_result_bytes = max_rows, max_result_bytes
        self.metrics = []
        self._closed = False
        self._active = {}
        conn = self._connection()
        try:
            self._schema_version = conn.execute("PRAGMA schema_version").fetchone()[0]
            if any(row[2] in {"virtual", "shadow"} for row in conn.execute("PRAGMA table_list")):
                raise ContractError("virtual tables require a separate execution policy")
            self._view_names = frozenset(row[0].casefold() for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"))
            tables = []
            for name, ddl in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                if ddl is None or "CREATE VIRTUAL" in ddl.upper():
                    raise ContractError("virtual tables require a separate execution policy")
                columns = [dict(zip(("cid", "name", "type", "notnull", "default", "pk"), row))
                           for row in conn.execute("PRAGMA table_info(" + _quoted(name) + ")")]
                foreign_keys = [dict(zip(("id", "seq", "table", "from", "to", "on_update", "on_delete", "match"), row))
                                for row in conn.execute("PRAGMA foreign_key_list(" + _quoted(name) + ")")]
                table = {"name": name, "ddl": ddl, "columns": columns, "foreign_keys": foreign_keys}
                if description_dir is not None:
                    folder = Path(description_dir)
                    if (folder / "database_description").is_dir():
                        folder = folder / "database_description"
                    description = folder / (name + ".csv")
                    # SQL identifiers need not be safe filenames. Only read a
                    # direct CSV in the supplied description directory.
                    if description.parent.resolve() == folder.resolve() and description.is_file() and description.resolve().parent == folder.resolve():
                        raw = description.read_bytes()
                        try:
                            content = raw.decode("utf-8-sig")
                        except UnicodeDecodeError:
                            content = raw.decode("cp1252")
                        table["descriptions"] = list(csv.DictReader(io.StringIO(content)))
                        table["description_sha256"] = hashlib.sha256(raw).hexdigest()
                tables.append(table)
            if not tables:
                raise ContractError("database has no permitted ordinary tables")
        finally:
            conn.close()
        self._tables = frozenset(t["name"].casefold() for t in tables)
        self._schema_payload = {"db_id": db_id, "tables": tables}
        encoded = json.dumps(self._schema_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.schema_id = hashlib.sha256(encoded.encode()).hexdigest()

    @property
    def schema_payload(self):
        return copy.deepcopy(self._schema_payload)

    def _connection(self):
        if not hasattr(sqlite3.Connection, "setconfig") or not hasattr(sqlite3, "SQLITE_DBCONFIG_DQS_DML"):
            raise ContractError("Python 3.12+ with SQLite DQS_DML configuration support is required")
        conn = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True,
                               timeout=min(self.timeout_s, 0.05))
        try:
            try:
                # Otherwise SQLite can silently treat an unknown quoted column
                # as a string literal, defeating real scope/column validation.
                conn.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)
                if conn.getconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML):
                    raise ContractError("SQLite DQS_DML must be disabled")
            except sqlite3.Error as exc:
                raise ContractError("SQLite runtime must support disabling DQS_DML") from exc
            conn.enable_load_extension(False)
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA trusted_schema=OFF")
            conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, self.max_result_bytes)
            conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_SQL_CHARS * 4)
            conn.execute("BEGIN")
        except BaseException:
            conn.close()
            raise
        return conn

    def _authorize(self, action, first, second, database, trigger, *, cte_names=frozenset()):
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            # SQLite reports an empty-column table read with database=None for
            # COUNT(*) and optimizer-elided column reads. No database is attached
            # and only known main tables qualify for this narrow callback form.
            local = database == "main" or (database is None and second == "")
            if local and str(first).casefold() in self._tables:
                return sqlite3.SQLITE_OK
            if database is None and second == "" and str(first).casefold() in cte_names:
                return sqlite3.SQLITE_OK
        elif action == sqlite3.SQLITE_FUNCTION and str(second or first).lower() in FUNCTIONS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def _prepare(self, conn, sql, control, deadline):
        if conn.execute("PRAGMA schema_version").fetchone()[0] != self._schema_version:
            raise ContractError("database schema changed; reopen the catalog")
        tree = _check_sql(sql)
        cte_names = frozenset(cte.alias_or_name.casefold() for cte in tree.find_all(exp.CTE))
        # An empty-column callback lacks database identity. Do not let an alias
        # impersonate an excluded physical object in another lexical scope.
        if any(name.startswith("sqlite_") or name in self._view_names for name in cte_names):
            raise ContractError("CTE names may not impersonate excluded database objects")
        conn.set_authorizer(lambda *args: self._authorize(*args, cte_names=cte_names))
        conn.set_progress_handler(lambda: int(control.cancelled.is_set() or time.perf_counter() > deadline), 1000)
        if control.cancelled.is_set():
            raise _QueryCancelled()
        conn.execute("EXPLAIN " + sql).fetchall()

    def validate(self, sql):
        if self._closed:
            raise ContractError("catalog is closed")
        _check_sql(sql)
        control = _Control()
        deadline = time.perf_counter() + self.timeout_s
        conn = self._connection()
        try:
            self._prepare(conn, sql, control, deadline)
        except sqlite3.Error as exc:
            if time.perf_counter() > deadline:
                raise TimeoutError("SQLite validation exceeded its deadline") from exc
            raise ContractError("SQLite rejected query scope, syntax, or permissions") from exc
        finally:
            conn.close()
        return Query(sql, self.db_id, self.schema_id)

    def _execute(self, sql, control):
        deadline = time.perf_counter() + self.timeout_s
        conn = self._connection()
        with control.lock:
            control.connection = conn
        try:
            self._prepare(conn, sql, control, deadline)
            cursor = conn.execute(sql)
            columns = [column[0] for column in cursor.description or ()]
            result, byte_count = [], 2
            for row in cursor:
                if control.cancelled.is_set():
                    raise _QueryCancelled()
                if time.perf_counter() > deadline:
                    raise TimeoutError("SQLite execution exceeded its deadline")
                if len(result) >= self.max_rows:
                    raise ContractError("result exceeds row bound; no partial result is returned")
                item = {"columns": columns.copy(), "values": list(row)}
                try:
                    serialized = json.dumps(item, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                except (TypeError, ValueError) as exc:
                    raise ContractError("result contains a non-JSON or nonfinite value") from exc
                byte_count += len(serialized.encode()) + bool(result)
                if byte_count > self.max_result_bytes:
                    raise ContractError("result exceeds byte bound; no partial result is returned")
                result.append(item)
            return result
        except sqlite3.Error as exc:
            if control.cancelled.is_set():
                raise _QueryCancelled() from exc
            if time.perf_counter() > deadline:
                raise TimeoutError("SQLite execution exceeded its deadline") from exc
            raise ContractError("SQLite rejected query scope, syntax, permissions, or result size") from exc
        finally:
            with control.lock:
                control.connection = None
                conn.close()

    @staticmethod
    async def _drain(worker, control):
        # Repeated coroutine cancellation must not abandon a live SQLite thread.
        while not worker.done():
            try:
                await asyncio.shield(worker)
            except asyncio.CancelledError:
                control.cancel()
            except Exception:
                break
        if not worker.cancelled():
            worker.exception()  # Consume worker errors even when the caller was cancelled.

    async def search(self, query):
        if self._closed:
            raise ContractError("catalog is closed")
        entry = {"operation": "sql_search", "db_id": self.db_id, "status": "error"}
        self.metrics.append(entry)
        started = time.perf_counter()
        worker = None
        try:
            if not isinstance(query, Query) or query.db_id != self.db_id or query.schema_id != self.schema_id:
                raise ContractError("query belongs to another database or schema")
            _check_sql(query.sql)
            entry["query"] = query.json()
            control = _Control()
            worker = asyncio.create_task(asyncio.to_thread(self._execute, query.sql, control))
            self._active[worker] = control
            try:
                result = await asyncio.shield(worker)
            except asyncio.CancelledError:
                control.cancel()
                await self._drain(worker, control)
                raise
            except _QueryCancelled as exc:
                raise asyncio.CancelledError() from exc
            entry.update(status="ok", rows=len(result))
            return result
        except asyncio.CancelledError:
            entry["status"] = "cancelled"
            raise
        except Exception as exc:
            entry["error"] = type(exc).__name__
            raise
        finally:
            if worker is not None:
                self._active.pop(worker, None)
            entry["elapsed_ms"] = (time.perf_counter() - started) * 1000

    async def close(self):
        self._closed = True
        active = list(self._active.items())
        for _, control in active:
            control.cancel()
        for worker, control in active:
            await self._drain(worker, control)
            self._active.pop(worker, None)
