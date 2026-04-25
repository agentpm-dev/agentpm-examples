from __future__ import annotations

import csv
import io
from collections import defaultdict
from pathlib import Path


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _load_rows(path: str | None, csv_text: str | None) -> list[dict[str, str]]:
    if bool(path) == bool(csv_text):
        raise ToolError("INPUT_INVALID", "Provide exactly one of path or csv_text")
    text = Path(path).read_text(encoding="utf-8") if path else csv_text or ""
    return list(csv.DictReader(io.StringIO(text)))


def _coerce(value: str):
    if value is None:
        return ""
    value = value.strip()
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _matches(row: dict[str, str], condition: dict) -> bool:
    lhs = row.get(condition.get("column", ""), "")
    rhs = condition.get("value")
    op = condition.get("op", "eq")
    left = _coerce(lhs)
    right = _coerce(str(rhs)) if rhs is not None else rhs
    if op == "eq":
        return left == right
    if op == "ne":
        return left != right
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "contains":
        return str(right) in str(left)
    raise ToolError("INPUT_INVALID", f"Unsupported filter op: {op}")


def _aggregate(rows: list[dict[str, str]], aggregations: list[dict]) -> dict[str, object]:
    out: dict[str, object] = {}
    for agg in aggregations:
        op = agg.get("op")
        column = agg.get("column")
        alias = agg.get("as") or f"{op}_{column or 'rows'}"
        values = [_coerce(row.get(column, "")) for row in rows] if column else []
        numeric = [value for value in values if isinstance(value, (int, float))]
        if op == "count":
            out[alias] = len(rows)
        elif op == "sum":
            out[alias] = sum(numeric)
        elif op == "avg":
            out[alias] = (sum(numeric) / len(numeric)) if numeric else 0
        elif op == "min":
            out[alias] = min(values) if values else None
        elif op == "max":
            out[alias] = max(values) if values else None
        else:
            raise ToolError("INPUT_INVALID", f"Unsupported aggregation op: {op}")
    return out


def query_csv(
    *,
    path: str | None = None,
    csv_text: str | None = None,
    select: list[str] | None = None,
    filter: list[dict] | None = None,
    sort: list[dict] | None = None,
    limit: int | None = None,
    group_by: list[str] | None = None,
    aggregations: list[dict] | None = None,
) -> dict:
    rows = _load_rows(path, csv_text)
    filters = filter or []
    for condition in filters:
        rows = [row for row in rows if _matches(row, condition)]

    for spec in reversed(sort or []):
        column = spec.get("column")
        reverse = spec.get("direction", "asc") == "desc"
        rows.sort(key=lambda row: _coerce(row.get(column, "")), reverse=reverse)

    if group_by:
        grouped: dict[tuple, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
          key = tuple(row.get(column, "") for column in group_by)
          grouped[key].append(row)
        result_rows: list[dict[str, object]] = []
        for key, group_rows in grouped.items():
            item: dict[str, object] = {column: value for column, value in zip(group_by, key)}
            item.update(_aggregate(group_rows, aggregations or [{"op": "count", "as": "count"}]))
            result_rows.append(item)
        rows_out = result_rows
        columns = list(rows_out[0].keys()) if rows_out else list(group_by)
    else:
        rows_out = rows
        columns = list(rows[0].keys()) if rows else []
        if aggregations:
            summary = _aggregate(rows, aggregations)
        else:
            summary = {"filtered": len(filters) > 0}

    if select:
        rows_out = [{column: row.get(column) for column in select} for row in rows_out]
        columns = select

    if limit is not None:
        rows_out = rows_out[:limit]

    if group_by:
        summary = {"group_by": group_by, "group_count": len(rows_out)}

    return {
        "columns": columns,
        "rows": rows_out,
        "row_count": len(rows_out),
        "summary": summary,
    }
