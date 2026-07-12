#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

try:
    from langchain_text_splitters import (
        MarkdownHeaderTextSplitter,
        RecursiveCharacterTextSplitter,
    )
except ImportError as exc:
    raise SystemExit(
        "langchain-text-splitters is required. Install it with "
        "`python3 -m pip install langchain-text-splitters` and rerun this script."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parents[2]
DOCS_ROOT = WORKSPACE_ROOT / "agentpm-api" / "docs" / "v0.1"
SOURCE_DOCS_ROOT = ROOT / "knowledge" / "source-docs" / "v0.1"
CHUNKS_PATH = ROOT / "knowledge" / "chunks.jsonl"
SOURCES_PATH = ROOT / "knowledge" / "sources.jsonl"
PROVENANCE_PATH = ROOT / "knowledge" / "provenance" / "sources-manifest.json"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
CHUNKING_STRATEGY = "langchain-markdown-headers-plus-recursive-character"

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n+", re.DOTALL)


@dataclass
class SourceDoc:
    source_id: str
    rel_path: Path
    title: str
    section: str
    description: str
    public_uri: str


def strip_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    metadata: dict[str, str] = {}
    if text.startswith("---\n"):
        match = FRONTMATTER_RE.match(text)
        if match:
            frontmatter = match.group(0)
            text = text[match.end():]
            for line in frontmatter.splitlines()[1:-1]:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
    return text.strip(), metadata


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "chunk"


HEADER_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "h2"), ("###", "h3"), ("####", "h4")],
    strip_headers=False,
)
BODY_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", " ", ""],
)


def split_into_langchain_chunks(markdown_text: str) -> list[tuple[str, str]]:
    docs = HEADER_SPLITTER.split_text(markdown_text)
    if not docs:
        docs = []

    pieces: list[tuple[str, str]] = []
    for doc in docs or []:
        section_value = (
            doc.metadata.get("h4")
            or doc.metadata.get("h3")
            or doc.metadata.get("h2")
            or "document-intro"
        )
        section_slug = slugify(section_value)
        text = normalize_text(doc.page_content)
        if not text:
            continue
        for split_doc in BODY_SPLITTER.create_documents([text]):
            piece = normalize_text(split_doc.page_content)
            if piece:
                pieces.append((section_slug, piece))

    if pieces:
        return pieces

    fallback_text = normalize_text(markdown_text)
    if not fallback_text:
        return []
    return [
        ("document-intro", normalize_text(doc.page_content))
        for doc in BODY_SPLITTER.create_documents([fallback_text])
        if normalize_text(doc.page_content)
    ]


def copy_source_docs() -> list[Path]:
    if SOURCE_DOCS_ROOT.exists():
        shutil.rmtree(SOURCE_DOCS_ROOT)
    shutil.copytree(DOCS_ROOT, SOURCE_DOCS_ROOT)
    return sorted(SOURCE_DOCS_ROOT.rglob("*.mdx"))


def build_source_doc(path: Path) -> SourceDoc:
    rel_path = path.relative_to(ROOT)
    rel_from_v1 = path.relative_to(SOURCE_DOCS_ROOT)
    raw = path.read_text(encoding="utf-8")
    _, metadata = strip_frontmatter(raw)
    title = metadata.get("title") or rel_from_v1.stem.replace("-", " ").title()
    section = metadata.get("section") or rel_from_v1.parts[0].replace("-", " ")
    description = metadata.get("description") or title
    slug = "/".join(rel_from_v1.with_suffix("").parts)
    public_uri = f"https://agentpackagemanager.com/docs/v0.1/{slug}"
    source_id = f"src_{slugify('-'.join(rel_from_v1.with_suffix('').parts))}"
    return SourceDoc(
        source_id=source_id,
        rel_path=rel_path,
        title=title,
        section=section,
        description=description,
        public_uri=public_uri,
    )


def build_records() -> tuple[list[dict], list[dict], list[dict]]:
    copied_docs = copy_source_docs()
    source_rows: list[dict] = []
    chunk_rows: list[dict] = []
    provenance_rows: list[dict] = []

    for path in copied_docs:
        source_doc = build_source_doc(path)
        raw = path.read_text(encoding="utf-8")
        body, metadata = strip_frontmatter(raw)
        body = normalize_text(body)
        split_chunks = split_into_langchain_chunks(body)

        source_rows.append(
            {
                "id": source_doc.source_id,
                "title": source_doc.title,
                "uri": source_doc.public_uri,
                "metadata": {
                    "path": source_doc.rel_path.as_posix(),
                    "section": source_doc.section,
                    "kind": "docs-mdx",
                    "frontmatter": metadata,
                },
            }
        )
        provenance_rows.append(
            {
                "id": source_doc.source_id,
                "path": source_doc.rel_path.as_posix(),
                "public_uri": source_doc.public_uri,
                "title": source_doc.title,
                "description": source_doc.description,
            }
        )

        chunk_index = 0
        for section_slug, piece in split_chunks:
            chunk_index += 1
            chunk_rows.append(
                {
                    "id": f"{source_doc.source_id}_chunk_{chunk_index}",
                    "source_id": source_doc.source_id,
                    "text": piece,
                    "metadata": {
                        "section": section_slug,
                        "source_path": source_doc.rel_path.as_posix(),
                        "title": source_doc.title,
                    },
                }
            )

    return source_rows, chunk_rows, provenance_rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_provenance(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "package": "@zack/agentpm-docs",
        "version": "0.1.0",
        "source_root": "agentpm-api/docs/v0.1",
        "copied_source_root": "knowledge/source-docs/v0.1",
        "chunking": {
            "strategy": CHUNKING_STRATEGY,
            "chunk_size": CHUNK_SIZE,
            "overlap": CHUNK_OVERLAP,
        },
        "builder": {
            "name": "agentpm-examples-agentpm-docs-pipeline",
            "version": "2026-07-12",
        },
        "sources": rows,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    if not DOCS_ROOT.exists():
        raise SystemExit(f"Docs root not found: {DOCS_ROOT}")
    sources, chunks, provenance = build_records()
    write_jsonl(SOURCES_PATH, sources)
    write_jsonl(CHUNKS_PATH, chunks)
    write_provenance(PROVENANCE_PATH, provenance)
    print(f"Copied source docs into {SOURCE_DOCS_ROOT}")
    print(f"Wrote {len(sources)} sources to {SOURCES_PATH}")
    print(f"Wrote {len(chunks)} chunks to {CHUNKS_PATH}")
    print(f"Wrote provenance manifest to {PROVENANCE_PATH}")


if __name__ == "__main__":
    main()
