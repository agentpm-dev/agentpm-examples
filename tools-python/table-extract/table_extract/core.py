from __future__ import annotations

import csv
import pathlib
from html.parser import HTMLParser


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = False
        self._in_cell = False
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in {"td", "th"}:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if self._in_table and tag in {"td", "th"} and self._current_row is not None:
            self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = []
            self._in_cell = False
        elif self._in_table and tag == "tr" and self._current_table is not None and self._current_row is not None:
            if any(cell for cell in self._current_row):
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            self.tables.append(self._current_table)
            self._current_table = None
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)


def _normalize_table(rows: list[list[str]], header_row: bool) -> dict:
    if not rows:
        return {"columns": [], "rows": []}
    if header_row:
        columns = rows[0]
        body = rows[1:]
    else:
        width = max(len(row) for row in rows)
        columns = [f"column_{index + 1}" for index in range(width)]
        body = rows
    normalized_rows = []
    for row in body:
        normalized_rows.append({column: row[index] if index < len(row) else "" for index, column in enumerate(columns)})
    return {"columns": columns, "rows": normalized_rows}


def _load_source(path: str | None, html_text: str | None, csv_text: str | None, source_type: str) -> tuple[str, str]:
    provided = [value is not None for value in [path, html_text, csv_text]]
    if sum(provided) != 1:
        raise ToolError("INPUT_INVALID", "Provide exactly one of path, html_text, or csv_text")
    if path is not None:
        file_path = pathlib.Path(path)
        if not file_path.exists():
            raise ToolError("INPUT_INVALID", f"File does not exist: {path}")
        text = file_path.read_text(encoding="utf-8")
        if source_type == "auto":
            source_type = "csv" if file_path.suffix.lower() == ".csv" else "html"
        return source_type, text
    if html_text is not None:
        return ("html" if source_type == "auto" else source_type), html_text
    return ("csv" if source_type == "auto" else source_type), csv_text or ""


def extract_tables(
    *,
    source_type: str = "auto",
    path: str | None = None,
    html_text: str | None = None,
    csv_text: str | None = None,
    table_index: int = 0,
    header_row: bool = True,
) -> dict:
    if source_type not in {"auto", "html", "csv"}:
        raise ToolError("INPUT_INVALID", "source_type must be auto, html, or csv")
    if table_index < 0:
        raise ToolError("INPUT_INVALID", "table_index must be >= 0")

    resolved_type, text = _load_source(path, html_text, csv_text, source_type)
    warnings: list[str] = []

    if resolved_type == "csv":
        rows = list(csv.reader(text.splitlines()))
        tables = [_normalize_table(rows, header_row)] if rows else []
        return {
            "tables": tables,
            "detected_count": len(tables),
            "warnings": warnings,
            "metadata": {"source_type": "csv"}
        }

    parser = _TableHTMLParser()
    parser.feed(text)
    detected_tables = parser.tables
    if not detected_tables:
        warnings.append("No HTML tables were detected.")
        tables = []
    elif table_index >= len(detected_tables):
        raise ToolError("INPUT_INVALID", f"table_index {table_index} is out of range for {len(detected_tables)} tables")
    else:
        tables = [_normalize_table(detected_tables[table_index], header_row)]

    return {
        "tables": tables,
        "detected_count": len(detected_tables),
        "warnings": warnings,
        "metadata": {"source_type": "html", "table_index": table_index}
    }
