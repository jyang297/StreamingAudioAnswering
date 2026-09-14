"""Bound database identities and plans; SQL permission lives in SQLiteCatalog."""
from __future__ import annotations

from dataclasses import dataclass


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Query:
    sql: str
    db_id: str
    schema_id: str

    def __post_init__(self):
        if any(not isinstance(value, str) or not value.strip()
               for value in (self.sql, self.db_id, self.schema_id)):
            raise ContractError("query requires SQL and a bound database/schema identity")

    def json(self):
        return {"sql": self.sql, "db_id": self.db_id, "schema_id": self.schema_id}


@dataclass(frozen=True)
class Plan:
    action: str
    query: Query | None

    def __post_init__(self):
        if not isinstance(self.action, str) or self.action not in {"retrieve", "wait"}:
            raise ContractError("builder must return retrieve or wait")
        if (self.action == "retrieve" and not isinstance(self.query, Query)) or (
                self.action == "wait" and self.query is not None):
            raise ContractError("retrieve requires Query; wait requires null")

    @classmethod
    def parse(cls, data, catalog):
        if not isinstance(data, dict) or set(data) != {"action", "query"}:
            raise ContractError("plan must contain exactly action and query")
        if data["action"] == "wait":
            return cls("wait", data["query"])
        query = data["query"]
        if data["action"] != "retrieve" or not isinstance(query, dict) or set(query) != {"sql"}:
            raise ContractError("retrieve query must contain exactly sql")
        return cls("retrieve", catalog.validate(query["sql"]))
