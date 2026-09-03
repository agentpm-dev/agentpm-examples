from __future__ import annotations

import os
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
    pgvector_query_values,
    provider_config,
    sql_identifier,
)

CONFIG = provider_config("pgvector-reference")


def retrieve(request: KnowledgeRuntimeRequest) -> KnowledgeRuntimeResult:
    try:
        import psycopg

        assert_attested_request(request, CONFIG)
        database_url = os.environ.get("PGVECTOR_DATABASE_URL")
        if not database_url:
            raise RuntimeError("PGVECTOR_DATABASE_URL is required")
        table = sql_identifier(
            os.environ.get("PGVECTOR_TABLE", "agentpm_m13_knowledge_chunks")
        )
        vector = openai_embed(request["query"], CONFIG)
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                      chunk_id,
                      source_id,
                      source_title,
                      source_uri,
                      text,
                      metadata,
                      1 - (embedding <=> %s::vector) AS score
                    FROM {table}
                    WHERE package_name = %s
                      AND package_version = %s
                      AND corpus_hash = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    pgvector_query_values(request, vector, CONFIG),
                )
                columns = [column.name for column in cursor.description]
                rows = [
                    dict(zip(columns, row, strict=True)) for row in cursor.fetchall()
                ]
        return normalize_external_rows(
            request,
            rows,
            return_citations_default=CONFIG.return_citations_default,
        )
    except Exception as exc:
        return failure_result(request, "pgvector_query_failed", str(exc))


def main() -> None:
    try:
        from agentpm import serve_knowledge_runtime_process
    except ImportError as exc:
        raise RuntimeError(
            "Installed agentpm SDK does not export serve_knowledge_runtime_process. "
            "Install a newer SDK release, or run this provider with "
            "`uv run --with-editable ../../../agentpm-sdk-python python "
            "providers/python/pgvector_runtime.py` for pre-publish milestone testing."
        ) from exc

    serve_knowledge_runtime_process(CONFIG.runtime_id, retrieve, capabilities(CONFIG))


if __name__ == "__main__":
    main()
