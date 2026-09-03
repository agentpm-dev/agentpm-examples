#!/usr/bin/env python3
from __future__ import annotations

import array
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "knowledge" / "chunks.jsonl"
OUTPUT_PATH = ROOT / "knowledge" / "embeddings" / "default.f32"
MODEL = os.environ.get("AGENTPM_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
URL = "https://api.openai.com/v1/embeddings"


def require_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required")
    return api_key


def read_chunks() -> list[str]:
    texts: list[str] = []
    with CHUNKS_PATH.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            row = json.loads(line)
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                raise SystemExit(f"{CHUNKS_PATH}:{line_number} missing non-empty text")
            texts.append(text)
    return texts


def request_embeddings(texts: list[str], api_key: str) -> list[list[float]]:
    body = json.dumps({"model": MODEL, "input": texts}).encode("utf-8")
    request = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, context=ssl.create_default_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenAI embeddings request failed: {exc.code} {detail}") from exc
    return [row["embedding"] for row in payload["data"]]


def write_vectors(vectors: list[list[float]]) -> None:
    if not vectors:
        raise SystemExit("No vectors returned")
    dimensions = len(vectors[0])
    if dimensions != 1536:
        raise SystemExit(f"Expected 1536 dimensions from {MODEL}, got {dimensions}")
    values = array.array("f")
    for vector in vectors:
        if len(vector) != dimensions:
            raise SystemExit("OpenAI returned inconsistent vector dimensions")
        values.extend(vector)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("wb") as handle:
        values.tofile(handle)
    print(f"Wrote {len(vectors)} vectors x {dimensions} dimensions to {OUTPUT_PATH}")


def main() -> None:
    write_vectors(request_embeddings(read_chunks(), require_api_key()))


if __name__ == "__main__":
    main()
