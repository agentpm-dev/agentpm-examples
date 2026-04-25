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
SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)", re.MULTILINE)


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
            sections.append(
                Section(
                    heading_path=headings.copy(),
                    text=section_text,
                    start_offset=buffer_start,
                )
            )
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


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _make_chunk_id(source_id: str | None, start: int, end: int, text: str) -> str:
    raw = f"{source_id or 'chunk'}:{start}:{end}:{text[:80]}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


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


def _sentence_units(text: str, start_offset: int) -> list[tuple[str, int]]:
    units: list[tuple[str, int]] = []
    for match in SENTENCE_RE.finditer(text):
        sentence = _normalize(match.group(0))
        if sentence:
            units.append((sentence, start_offset + match.start()))
    return units or [(text.strip(), start_offset)]


def _window_units(text: str, start_offset: int, max_chars: int) -> list[tuple[str, int]]:
    cleaned = text.strip()
    if not cleaned:
        return []
    units: list[tuple[str, int]] = []
    local_start = 0
    while local_start < len(cleaned):
        local_end = min(local_start + max_chars, len(cleaned))
        if local_end < len(cleaned):
            split_at = cleaned.rfind(" ", local_start, local_end)
            if split_at > local_start + 20:
                local_end = split_at
        unit = cleaned[local_start:local_end].strip()
        if unit:
            units.append((unit, start_offset + local_start))
        local_start = local_end
        while local_start < len(cleaned) and cleaned[local_start].isspace():
            local_start += 1
    return units


def _expand_unit(unit_text: str, unit_start: int, max_chars: int) -> list[tuple[str, int]]:
    if len(unit_text) <= max_chars:
        return [(unit_text, unit_start)]

    sentences = _sentence_units(unit_text, unit_start)
    if len(sentences) > 1:
        expanded: list[tuple[str, int]] = []
        for sentence_text, sentence_start in sentences:
            if len(sentence_text) <= max_chars:
                expanded.append((sentence_text, sentence_start))
            else:
                expanded.extend(_window_units(sentence_text, sentence_start, max_chars))
        return expanded

    return _window_units(unit_text, unit_start, max_chars)


def _resolve_units(section: Section, strategy: str, max_chars: int) -> list[tuple[str, int]]:
    if strategy == "heading" and len(section.text) <= max_chars:
        return [(section.text, section.start_offset)]

    units: list[tuple[str, int]] = []
    for unit_text, unit_start in _paragraph_units(section):
        units.extend(_expand_unit(unit_text, unit_start, max_chars))
    return units or [(section.text[:max_chars], section.start_offset)]


def _emit_chunk(
    chunks: list[dict],
    *,
    heading_path: list[str],
    current_text: str,
    current_start: int,
    source_id: str | None,
) -> None:
    chunk_text = current_text.strip()
    if not chunk_text:
        return
    end = current_start + len(chunk_text)
    chunks.append(
        {
            "id": _make_chunk_id(source_id, current_start, end, chunk_text),
            "text": chunk_text,
            "heading_path": heading_path,
            "start_offset": current_start,
            "end_offset": end,
            "char_count": len(chunk_text),
            **({"source_id": source_id} if source_id else {}),
        }
    )


def _compose_with_overlap(prefix: str, unit_text: str, max_chars: int) -> tuple[str, int]:
    if not prefix:
        return unit_text, 0

    separator_len = 1
    max_prefix = max_chars - len(unit_text) - separator_len
    if max_prefix <= 0:
        return unit_text, 0

    trimmed_prefix = prefix[-max_prefix:]
    return f"{trimmed_prefix}\n{unit_text}".strip(), len(trimmed_prefix)


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
    if overlap >= max_chars:
        raise ToolError("INPUT_INVALID", "overlap must be smaller than max_chars")

    sections = _build_sections(text)
    chunks: list[dict] = []

    for section in sections:
        units = _resolve_units(section, strategy, max_chars)
        current = ""
        current_start = section.start_offset

        for unit_text, unit_start in units:
            candidate = unit_text if not current else f"{current}\n\n{unit_text}"
            if current and len(candidate) > max_chars:
                _emit_chunk(
                    chunks,
                    heading_path=section.heading_path,
                    current_text=current,
                    current_start=current_start,
                    source_id=source_id,
                )
                emitted_text = chunks[-1]["text"]
                prefix = emitted_text[-overlap:] if overlap else ""
                current, prefix_len = _compose_with_overlap(prefix, unit_text, max_chars)
                current_start = chunks[-1]["end_offset"] - prefix_len if prefix_len else unit_start
            else:
                if not current:
                    current_start = unit_start
                current = candidate

        if current.strip():
            _emit_chunk(
                chunks,
                heading_path=section.heading_path,
                current_text=current,
                current_start=current_start,
                source_id=source_id,
            )

    return {
        "chunks": chunks,
        "metadata": {
            "chunk_count": len(chunks),
            "strategy": strategy,
            "max_chars": max_chars,
            "overlap": overlap,
            "fallback_order": ["heading", "paragraph", "sentence", "window"],
        },
    }
