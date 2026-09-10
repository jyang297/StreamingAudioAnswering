from __future__ import annotations

import math
from dataclasses import asdict, dataclass


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Query:
    name: str | None = None
    category_id: int | None = None
    min_price: float | None = None
    max_price: float | None = None
    in_stock: bool | None = None
    discontinued: bool | None = None
    order: str = "product_id"
    limit: int = 10

    @classmethod
    def parse(cls, data):
        if not isinstance(data, dict) or set(data) - set(cls.__dataclass_fields__):
            raise ContractError("query must contain only supported catalog fields")
        q = cls(**data)
        if q.name is not None and (not isinstance(q.name, str) or not q.name.strip()
                                   or len(q.name) > 120):
            raise ContractError("invalid name")
        if q.category_id is not None and (type(q.category_id) is not int or q.category_id < 1):
            raise ContractError("invalid category_id")
        for value in (q.min_price, q.max_price):
            if value is not None and (type(value) not in (int, float)
                                      or not math.isfinite(value) or value < 0):
                raise ContractError("invalid price")
        if q.min_price is not None and q.max_price is not None and q.min_price > q.max_price:
            raise ContractError("invalid price range")
        if any(x is not None and type(x) is not bool for x in (q.in_stock, q.discontinued)):
            raise ContractError("invalid boolean filter")
        if type(q.limit) is not int or not 1 <= q.limit <= 20:
            raise ContractError("limit must be 1..20")
        if q.order not in ("product_id", "price_asc", "price_desc"):
            raise ContractError("unsupported order")
        return q

    def json(self):
        return asdict(self)


@dataclass(frozen=True)
class Plan:
    action: str
    query: Query | None

    @classmethod
    def parse(cls, data):
        if not isinstance(data, dict) or data.get("action") not in ("retrieve", "wait"):
            raise ContractError("builder must return retrieve or wait")
        if set(data) - {"action", "query"}:
            raise ContractError("unsupported builder fields")
        if data["action"] == "wait":
            if data.get("query") is not None:
                raise ContractError("wait must not contain a query")
            return cls("wait", None)
        return cls("retrieve", Query.parse(data.get("query")))


@dataclass
class Evidence:
    query: Query
    rows: list[dict]
    error: str | None = None


CATALOG_SCHEMA = """Only northwind_products is available. Query JSON fields (all optional):
name: literal product-name substring; category_id: positive integer;
min_price/max_price: nonnegative numbers; in_stock/discontinued: booleans;
order: product_id|price_asc|price_desc; limit: 1..20 (default 10).
Rows expose product_id, product_name, category_id, unit_price, units_in_stock,
quantity_per_unit, discontinued. Never invent category IDs or missing entities.
This is a historical sample catalog, not current prices. Never output SQL."""
