from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentpm import KnowledgeRuntimeRequest, KnowledgeRuntimeResult
else:
    KnowledgeRuntimeRequest = dict[str, Any]
    KnowledgeRuntimeResult = dict[str, Any]


@dataclass(frozen=True)
class ProviderConfig:
    runtime_id: str
    package_name: str
    version: str
    corpus: str
    embedding_provider: str
    embedding_model: str
    dimensions: int
    return_citations_default: bool


def provider_config(default_runtime_id: str) -> ProviderConfig:
    return_citations_default = os.environ.get("AGENTPM_KNOWLEDGE_RETURN_CITATIONS")
    return ProviderConfig(
        runtime_id=os.environ.get("AGENTPM_KNOWLEDGE_RUNTIME_ID", default_runtime_id),
        package_name=os.environ.get(
            "AGENTPM_KNOWLEDGE_PACKAGE", "@zack/m13-reference-corpus"
        ),
        version=os.environ.get("AGENTPM_KNOWLEDGE_VERSION", "0.1.0"),
        corpus=os.environ.get("AGENTPM_KNOWLEDGE_CORPUS_HASH", ""),
        embedding_provider=os.environ.get("AGENTPM_EMBEDDING_PROVIDER", "openai"),
        embedding_model=os.environ.get(
            "AGENTPM_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        dimensions=int(os.environ.get("AGENTPM_EMBEDDING_DIMENSIONS", "1536")),
        return_citations_default=(
            True
            if return_citations_default is None
            else return_citations_default.lower() != "false"
        ),
    )


def capabilities(config: ProviderConfig) -> dict[str, Any]:
    return {
        "modes": ["vector_query"],
        "features": ["citations"],
        "packages": [
            {
                "package": config.package_name,
                "version": config.version,
                "corpus": config.corpus,
                "ready": bool(config.corpus),
            }
        ],
    }


def assert_attested_request(
    request: KnowledgeRuntimeRequest, config: ProviderConfig
) -> None:
    if request["package"] != config.package_name:
        raise RuntimeError(
            f"request package {request['package']} does not match {config.package_name}"
        )
    if request["version"] != config.version:
        raise RuntimeError(
            f"request version {request['version']} does not match {config.version}"
        )
    if request["mode"] != "vector_query":
        raise RuntimeError(f"unsupported Knowledge mode {request['mode']}")
    if not request.get("query"):
        raise RuntimeError("vector_query request requires query")
    if not config.corpus:
        raise RuntimeError(
            "AGENTPM_KNOWLEDGE_CORPUS_HASH is required for package attestation"
        )


def failure_result(
    request: KnowledgeRuntimeRequest, code: str, message: str
) -> KnowledgeRuntimeResult:
    return {
        "ok": False,
        "package": request["package"],
        "version": request["version"],
        "mode": request["mode"],
        "query": request.get("query"),
        "error": {"code": code, "message": message, "retryable": False},
    }


def request_top_k(request: KnowledgeRuntimeRequest, default_top_k: int = 3) -> int:
    top_k = request.get("top_k")
    return top_k if isinstance(top_k, int) and top_k > 0 else default_top_k


def pinecone_query_body(
    request: KnowledgeRuntimeRequest,
    vector: list[float],
    config: ProviderConfig,
    namespace: str = "",
) -> dict[str, Any]:
    return {
        "namespace": namespace,
        "vector": vector,
        "topK": request_top_k(request),
        "includeMetadata": True,
        "filter": {
            "package": {"$eq": config.package_name},
            "version": {"$eq": config.version},
            "corpus": {"$eq": config.corpus},
        },
    }


def sql_identifier(value: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        raise RuntimeError(f"unsafe SQL identifier {value}")
    return value


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"


def pgvector_query_values(
    request: KnowledgeRuntimeRequest, vector: list[float], config: ProviderConfig
) -> tuple[str, str, str, str, str, int]:
    literal = vector_literal(vector)
    return (
        literal,
        config.package_name,
        config.version,
        config.corpus,
        literal,
        request_top_k(request),
    )


def normalize_external_rows(
    request: KnowledgeRuntimeRequest,
    rows: list[dict[str, Any]],
    *,
    return_citations_default: bool = True,
) -> KnowledgeRuntimeResult:
    results: list[dict[str, Any]] = []
    threshold = request.get("score_threshold")
    for row in rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        result = {
            "rank": 0,
            "score": float(row.get("score") or 0),
            "chunk_id": str(row.get("chunk_id") or metadata.get("chunk_id")),
            "source_id": str(row.get("source_id") or metadata.get("source_id")),
            "chunk_metadata": metadata.get("chunk_metadata") or metadata,
        }
        source_title = (
            row.get("source_title")
            or metadata.get("source_title")
            or metadata.get("title")
        )
        source_uri = (
            row.get("source_uri") or metadata.get("source_uri") or metadata.get("uri")
        )
        text = row.get("text") or metadata.get("text")
        if source_title:
            result["source_title"] = source_title
        if source_uri:
            result["source_uri"] = source_uri
        if text:
            result["text"] = text
        if metadata.get("source_metadata"):
            result["source_metadata"] = metadata["source_metadata"]
        if isinstance(threshold, int | float) and result["score"] < threshold:
            continue
        results.append(result)
    for index, result in enumerate(results, start=1):
        result["rank"] = index
    include_citations = request.get("return_citations", return_citations_default)
    return {
        "ok": True,
        "package": request["package"],
        "version": request["version"],
        "mode": request["mode"],
        "query": request.get("query"),
        "results": results,
        "citations": (
            [
                {
                    "chunk_id": result["chunk_id"],
                    "source_id": result["source_id"],
                    "title": result.get("source_title"),
                    "uri": result.get("source_uri"),
                }
                for result in results
            ]
            if include_citations
            else []
        ),
    }


def pinecone_matches_to_rows(
    matches: list[dict[str, Any]], config: ProviderConfig
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in matches:
        metadata = (
            match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
        )
        if metadata.get("package") != config.package_name:
            raise RuntimeError(
                f"Pinecone match {match.get('id')} has mismatched package metadata"
            )
        if metadata.get("version") != config.version:
            raise RuntimeError(
                f"Pinecone match {match.get('id')} has mismatched version metadata"
            )
        if metadata.get("corpus") != config.corpus:
            raise RuntimeError(
                f"Pinecone match {match.get('id')} has mismatched corpus metadata"
            )
        rows.append(
            {
                "score": match.get("score"),
                "chunk_id": metadata.get("chunk_id") or match.get("id"),
                "source_id": metadata.get("source_id"),
                "source_title": metadata.get("source_title"),
                "source_uri": metadata.get("source_uri"),
                "text": metadata.get("text"),
                "metadata": metadata,
            }
        )
    return rows


def openai_embed(text: str, config: ProviderConfig) -> list[float]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    body = json.dumps({"model": config.embedding_model, "input": text}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, context=ssl.create_default_context()
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"OpenAI embedding request failed with HTTP {exc.code}"
        ) from exc
    vector = payload["data"][0]["embedding"]
    if len(vector) != config.dimensions:
        raise RuntimeError(
            f"OpenAI embedding dimensions did not match {config.dimensions}"
        )
    return vector
