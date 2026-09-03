#!/usr/bin/env python3
from __future__ import annotations

import argparse
import array
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upsert an AgentPM vector Knowledge package into Pinecone."
    )
    parser.add_argument("package_root", type=Path)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_vectors(path: Path, count: int, dimensions: int) -> list[list[float]]:
    values = array.array("f")
    with path.open("rb") as handle:
        values.fromfile(handle, count * dimensions)
    if len(values) != count * dimensions:
        raise SystemExit(
            f"{path} does not contain {count} x {dimensions} float32 values"
        )
    return [
        list(values[index * dimensions : (index + 1) * dimensions])
        for index in range(count)
    ]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def main() -> None:
    args = parse_args()
    manifest = json.loads(
        (args.package_root / "agent.json").read_text(encoding="utf-8")
    )
    knowledge = manifest["knowledge"]
    corpus = knowledge["corpus"]
    embedding = knowledge["embedding"]
    corpus_hash = corpus.get("content_hash")
    if not corpus_hash:
        raise SystemExit(
            "Run `agentpm knowledge build` before upserting Pinecone so corpus.content_hash exists"
        )
    package_name = f"@zack/{manifest['name']}"
    chunks = read_jsonl(args.package_root / corpus["chunks_path"])
    sources = {
        row["id"]: row for row in read_jsonl(args.package_root / corpus["sources_path"])
    }
    vectors = read_vectors(
        args.package_root / embedding["vectors_path"],
        len(chunks),
        int(embedding["dimensions"]),
    )
    pinecone_vectors = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        source = sources[chunk["source_id"]]
        pinecone_vectors.append(
            {
                "id": chunk["id"],
                "values": vector,
                "metadata": {
                    **(chunk.get("metadata") or {}),
                    "package": package_name,
                    "version": manifest["version"],
                    "corpus": corpus_hash,
                    "chunk_id": chunk["id"],
                    "source_id": chunk["source_id"],
                    "source_title": source.get("title"),
                    "source_uri": source.get("uri"),
                    "text": chunk["text"],
                },
            }
        )

    body = json.dumps(
        {
            "namespace": os.environ.get("PINECONE_NAMESPACE", ""),
            "vectors": pinecone_vectors,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        require_env("PINECONE_INDEX_HOST").rstrip("/") + "/vectors/upsert",
        data=body,
        headers={
            "Api-Key": require_env("PINECONE_API_KEY"),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Pinecone upsert failed: HTTP {exc.code} {detail}") from exc
    print(f"Upserted {len(pinecone_vectors)} vectors into Pinecone")


if __name__ == "__main__":
    main()
