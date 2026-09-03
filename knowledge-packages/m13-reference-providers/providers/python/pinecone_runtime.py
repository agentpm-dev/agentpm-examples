from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentpm import KnowledgeRuntimeRequest, KnowledgeRuntimeResult
else:
    KnowledgeRuntimeRequest = dict[str, Any]
    KnowledgeRuntimeResult = dict[str, Any]

from reference_runtime import (
    assert_attested_request,
    capabilities,
    failure_result,
    normalize_external_rows,
    openai_embed,
    pinecone_query_body,
    pinecone_matches_to_rows,
    provider_config,
)

CONFIG = provider_config("pinecone-reference")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def retrieve(request: KnowledgeRuntimeRequest) -> KnowledgeRuntimeResult:
    try:
        assert_attested_request(request, CONFIG)
        vector = openai_embed(request["query"], CONFIG)
        body = json.dumps(
            pinecone_query_body(
                request,
                vector,
                CONFIG,
                os.environ.get("PINECONE_NAMESPACE", ""),
            )
        ).encode("utf-8")
        url = require_env("PINECONE_INDEX_HOST").rstrip("/") + "/query"
        pinecone_request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Api-Key": require_env("PINECONE_API_KEY"),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(pinecone_request) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Pinecone query failed with HTTP {exc.code}") from exc
        return normalize_external_rows(
            request,
            pinecone_matches_to_rows(payload.get("matches", []), CONFIG),
            return_citations_default=CONFIG.return_citations_default,
        )
    except Exception as exc:
        return failure_result(request, "pinecone_query_failed", str(exc))


def main() -> None:
    try:
        from agentpm import serve_knowledge_runtime_process
    except ImportError as exc:
        raise RuntimeError(
            "Installed agentpm SDK does not export serve_knowledge_runtime_process. "
            "Install a newer SDK release, or run this provider with "
            "`uv run --with-editable ../../../agentpm-sdk-python python "
            "providers/python/pinecone_runtime.py` for pre-publish milestone testing."
        ) from exc

    serve_knowledge_runtime_process(CONFIG.runtime_id, retrieve, capabilities(CONFIG))


if __name__ == "__main__":
    main()
