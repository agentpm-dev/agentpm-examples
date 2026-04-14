from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


class ToolError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass
class Section:
    heading_path: list[str]
    text: str
    start_offset: int


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _build_sections(text: str) -> list[Section]:
    lines = text.splitlines(keepends=True)
    sections: list[Section] = []
    headings: list[str] = []
    buffer: list[str] = []
    buffer_start = 0
    offset = 0

    def flush() -> None:
      nonlocal buffer, buffer_start
      section_text = "".join(buffer).strip()
      if section_text:
          sections.append(Section(heading_path=headings.copy(), text=section_text, start_offset=buffer_start))
      buffer = []

    for line in lines:
        match = HEADING_RE.match(line.strip())
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            headings[:] = headings[: level - 1]
            headings.append(title)
            buffer_start = offset + len(line)
        else:
            if not buffer:
                buffer_start = offset
            buffer.append(line)
        offset += len(line)

    flush()
    if not sections and text.strip():
        sections.append(Section(heading_path=[], text=text.strip(), start_offset=0))
    return sections


def _paragraph_units(section: Section) -> list[tuple[str, int]]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", section.text) if part.strip()]
    units: list[tuple[str, int]] = []
    cursor = section.start_offset
    for part in parts:
        idx = section.text.find(part, max(cursor - section.start_offset, 0))
        start = section.start_offset + max(idx, 0)
        units.append((part, start))
        cursor = start + len(part)
    return units or [(section.text, section.start_offset)]


def _make_chunk_id(source_id: str | None, start: int, end: int, text: str) -> str:
    raw = f"{source_id or 'chunk'}:{start}:{end}:{text[:80]}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


def chunk_markdown(
    *,
    text: str,
    strategy: str = "hybrid",
    max_chars: int = 1200,
    overlap: int = 150,
    source_id: str | None = None,
) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ToolError("INPUT_INVALID", "text must be a non-empty string")
    if strategy not in {"heading", "paragraph", "hybrid"}:
        raise ToolError("INPUT_INVALID", "strategy must be heading, paragraph, or hybrid")
    if max_chars < 100:
        raise ToolError("INPUT_INVALID", "max_chars must be >= 100")
    if overlap < 0:
        raise ToolError("INPUT_INVALID", "overlap must be >= 0")

    sections = _build_sections(text)
    chunks: list[dict] = []

    for section in sections:
        if strategy == "heading" and len(section.text) <= max_chars:
            units = [(section.text, section.start_offset)]
        else:
            units = _paragraph_units(section)

        current = ""
        current_start = section.start_offset
        for unit_text, unit_start in units:
            candidate = unit_text if not current else f"{current}\n\n{unit_text}"
            if current and len(candidate) > max_chars:
                chunk_text = current.strip()
                end = current_start + len(chunk_text)
                chunks.append(
                    {
                        "id": _make_chunk_id(source_id, current_start, end, chunk_text),
                        "text": chunk_text,
                        "heading_path": section.heading_path,
                        "start_offset": current_start,
                        "end_offset": end,
                        "char_count": len(chunk_text),
                        **({"source_id": source_id} if source_id else {}),
                    }
                )
                prefix = chunk_text[-overlap:] if overlap else ""
                current = f"{prefix}\n{unit_text}".strip() if prefix else unit_text
                current_start = max(end - len(prefix), unit_start if not prefix else end - len(prefix))
            else:
                if not current:
                    current_start = unit_start
                current = candidate

        if current.strip():
            chunk_text = current.strip()
            end = current_start + len(chunk_text)
            chunks.append(
                {
                    "id": _make_chunk_id(source_id, current_start, end, chunk_text),
                    "text": chunk_text,
                    "heading_path": section.heading_path,
                    "start_offset": current_start,
                    "end_offset": end,
                    "char_count": len(chunk_text),
                    **({"source_id": source_id} if source_id else {}),
                }
            )

    return {
        "chunks": chunks,
        "metadata": {
            "chunk_count": len(chunks),
            "strategy": strategy,
            "max_chars": max_chars,
            "overlap": overlap,
        },
    }
