from __future__ import annotations

import csv
import html
import json
import mimetypes
import re
from html.parser import HTMLParser
from pathlib import Path


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _HTMLToMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.link_stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag in {"p", "div", "section", "article", "main", "br", "li"}:
            self.parts.append("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append(f"\n{'#' * int(tag[1])} ")
        elif tag == "a":
            self.link_stack.append(attrs_map.get("href"))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "section", "article", "main", "li"}:
            self.parts.append("\n")
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else None
            if href:
                self.parts.append(f" ({href})")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def render(self) -> str:
        text = "".join(self.parts)
        text = html.unescape(text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _guess_media_type(path: Path) -> str:
    media_type, _ = mimetypes.guess_type(path.name)
    if media_type:
        return media_type
    suffix = path.suffix.lower()
    mapping = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json",
        ".csv": "text/csv"
    }
    return mapping.get(suffix, "application/octet-stream")


def _html_to_markdown(text: str) -> str:
    parser = _HTMLToMarkdownParser()
    parser.feed(text)
    return parser.render()


def _html_to_text(text: str) -> str:
    parser = _HTMLToMarkdownParser()
    parser.feed(text)
    markdown = parser.render()
    return re.sub(r"[#*`>\-]", "", markdown).strip()


def _csv_to_markdown(text: str) -> str:
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    parts = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in body:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def _csv_to_text(text: str) -> str:
    rows = list(csv.reader(text.splitlines()))
    return "\n".join(", ".join(row) for row in rows)


def _json_to_markdown(text: str) -> str:
    payload = json.loads(text)
    return "```json\n" + json.dumps(payload, indent=2, ensure_ascii=False) + "\n```"


def _json_to_text(text: str) -> str:
    payload = json.loads(text)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def convert_document(*, path: str, to_format: str = "markdown", extract_metadata: bool = True) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise ToolError("INPUT_INVALID", f"File does not exist: {path}")
    if not file_path.is_file():
        raise ToolError("INPUT_INVALID", f"Path is not a file: {path}")
    if to_format not in {"markdown", "text"}:
        raise ToolError("INPUT_INVALID", "to_format must be markdown or text")

    raw_text = file_path.read_text(encoding="utf-8")
    media_type = _guess_media_type(file_path)
    suffix = file_path.suffix.lower()

    if suffix in {".md", ".txt"}:
        content = raw_text
    elif suffix in {".html", ".htm"}:
        content = _html_to_markdown(raw_text) if to_format == "markdown" else _html_to_text(raw_text)
    elif suffix == ".csv":
        content = _csv_to_markdown(raw_text) if to_format == "markdown" else _csv_to_text(raw_text)
    elif suffix == ".json":
        content = _json_to_markdown(raw_text) if to_format == "markdown" else _json_to_text(raw_text)
    else:
        raise ToolError("UNSUPPORTED_TYPE", f"Unsupported file type: {suffix or media_type}")

    metadata = {}
    if extract_metadata:
        stat = file_path.stat()
        metadata = {
            "file_name": file_path.name,
            "size_bytes": stat.st_size,
            "line_count": len(raw_text.splitlines()),
            "output_format": to_format
        }

    return {
      "path": str(file_path),
      "media_type": media_type,
      "content": content,
      "metadata": metadata
    }
