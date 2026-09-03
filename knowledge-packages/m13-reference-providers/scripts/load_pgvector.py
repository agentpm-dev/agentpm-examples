#!/usr/bin/env python3
from __future__ import annotations

import argparse
import array
import json
import os
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load an AgentPM vector Knowledge package into pgvector."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--create-schema", action="store_true")
    parser.add_argument(
        "--table",
        default=os.environ.get("PGVECTOR_TABLE", "agentpm_m13_knowledge_chunks"),
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sql_identifier(value: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        raise SystemExit(f"unsafe SQL identifier {value}")
    return value


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


def main() -> None:
    args = parse_args()
    table = sql_identifier(args.table)
    database_url = os.environ.get("PGVECTOR_DATABASE_URL")
    if not database_url:
        raise SystemExit("PGVECTOR_DATABASE_URL is required")
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit(
            "Install psycopg first: uv add 'psycopg[binary]>=3.2.0'"
        ) from exc

    manifest = json.loads(
        (args.package_root / "agent.json").read_text(encoding="utf-8")
    )
    knowledge = manifest["knowledge"]
    corpus = knowledge["corpus"]
    embedding = knowledge["embedding"]
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
    corpus_hash = corpus.get("content_hash")
    if not corpus_hash:
        raise SystemExit(
            "Run `agentpm knowledge build` before loading pgvector so corpus.content_hash exists"
        )

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            if args.create_schema:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                      package_name text NOT NULL,
                      package_version text NOT NULL,
                      corpus_hash text NOT NULL,
                      chunk_id text PRIMARY KEY,
                      source_id text NOT NULL,
                      source_title text,
                      source_uri text,
                      text text NOT NULL,
                      metadata jsonb NOT NULL,
                      embedding vector({int(embedding["dimensions"])}) NOT NULL
                    )
                    """)
            for chunk, vector in zip(chunks, vectors, strict=True):
                source = sources[chunk["source_id"]]
                metadata = {
                    **(chunk.get("metadata") or {}),
                    "package": package_name,
                    "version": manifest["version"],
                    "corpus": corpus_hash,
                    "chunk_id": chunk["id"],
                    "source_id": chunk["source_id"],
                    "source_title": source.get("title"),
                    "source_uri": source.get("uri"),
                    "text": chunk["text"],
                }
                cursor.execute(
                    f"""
                    INSERT INTO {table}
                      (package_name, package_version, corpus_hash, chunk_id, source_id, source_title, source_uri, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                      package_name = EXCLUDED.package_name,
                      package_version = EXCLUDED.package_version,
                      corpus_hash = EXCLUDED.corpus_hash,
                      source_id = EXCLUDED.source_id,
                      source_title = EXCLUDED.source_title,
                      source_uri = EXCLUDED.source_uri,
                      text = EXCLUDED.text,
                      metadata = EXCLUDED.metadata,
                      embedding = EXCLUDED.embedding
                    """,
                    (
                        package_name,
                        manifest["version"],
                        corpus_hash,
                        chunk["id"],
                        chunk["source_id"],
                        source.get("title"),
                        source.get("uri"),
                        chunk["text"],
                        json.dumps(metadata),
                        "[" + ",".join(str(value) for value in vector) + "]",
                    ),
                )
        connection.commit()
    print(f"Loaded {len(chunks)} chunks into {table}")


if __name__ == "__main__":
    main()
