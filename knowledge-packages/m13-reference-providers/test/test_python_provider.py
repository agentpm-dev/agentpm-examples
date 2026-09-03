from __future__ import annotations

import pytest

import pgvector_runtime
import pinecone_runtime
from reference_runtime import (
    ProviderConfig,
    capabilities,
    failure_result,
    normalize_external_rows,
    pgvector_query_values,
    pinecone_query_body,
    pinecone_matches_to_rows,
    sql_identifier,
    vector_literal,
)

CONFIG = ProviderConfig(
    runtime_id="pinecone-reference",
    package_name="@zack/m13-reference-corpus",
    version="0.1.0",
    corpus="sha256:test-corpus",
    embedding_provider="openai",
    embedding_model="text-embedding-3-small",
    dimensions=1536,
    return_citations_default=True,
)


def test_capabilities_advertise_exact_package_corpus_attestation() -> None:
    assert capabilities(CONFIG) == {
        "modes": ["vector_query"],
        "features": ["citations"],
        "packages": [
            {
                "package": "@zack/m13-reference-corpus",
                "version": "0.1.0",
                "corpus": "sha256:test-corpus",
                "ready": True,
            }
        ],
    }


def test_pinecone_metadata_maps_to_normalized_knowledge_results_and_citations() -> None:
    request = {
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "return_citations": True,
    }
    rows = pinecone_matches_to_rows(
        [
            {
                "id": "chunk_release_gate",
                "score": 0.99,
                "metadata": {
                    "package": "@zack/m13-reference-corpus",
                    "version": "0.1.0",
                    "corpus": "sha256:test-corpus",
                    "chunk_id": "chunk_release_gate",
                    "source_id": "src_ops_playbook",
                    "source_title": "Alpha Operations Playbook",
                    "source_uri": "agentpm://examples/m13/alpha-ops",
                    "text": "release gate",
                },
            }
        ],
        CONFIG,
    )
    assert normalize_external_rows(request, rows) == {
        "ok": True,
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "results": [
            {
                "rank": 1,
                "score": 0.99,
                "chunk_id": "chunk_release_gate",
                "source_id": "src_ops_playbook",
                "source_title": "Alpha Operations Playbook",
                "source_uri": "agentpm://examples/m13/alpha-ops",
                "text": "release gate",
                "chunk_metadata": {
                    "package": "@zack/m13-reference-corpus",
                    "version": "0.1.0",
                    "corpus": "sha256:test-corpus",
                    "chunk_id": "chunk_release_gate",
                    "source_id": "src_ops_playbook",
                    "source_title": "Alpha Operations Playbook",
                    "source_uri": "agentpm://examples/m13/alpha-ops",
                    "text": "release gate",
                },
            }
        ],
        "citations": [
            {
                "chunk_id": "chunk_release_gate",
                "source_id": "src_ops_playbook",
                "title": "Alpha Operations Playbook",
                "uri": "agentpm://examples/m13/alpha-ops",
            }
        ],
    }


def test_omitted_return_citations_follows_package_retrieval_default() -> None:
    request = {
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
    }
    rows = [
        {
            "score": 0.99,
            "chunk_id": "chunk_release_gate",
            "source_id": "src_ops_playbook",
            "source_title": "Alpha Operations Playbook",
            "source_uri": "agentpm://examples/m13/alpha-ops",
            "text": "release gate",
            "metadata": {},
        }
    ]
    assert normalize_external_rows(
        request,
        rows,
        return_citations_default=True,
    )["citations"] == [
        {
            "chunk_id": "chunk_release_gate",
            "source_id": "src_ops_playbook",
            "title": "Alpha Operations Playbook",
            "uri": "agentpm://examples/m13/alpha-ops",
        }
    ]
    assert (
        normalize_external_rows(
            request,
            rows,
            return_citations_default=False,
        )["citations"]
        == []
    )


def test_explicit_return_citations_false_suppresses_citations() -> None:
    request = {
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "return_citations": False,
    }
    rows = [
        {
            "score": 0.99,
            "chunk_id": "chunk_release_gate",
            "source_id": "src_ops_playbook",
            "source_title": "Alpha Operations Playbook",
            "source_uri": "agentpm://examples/m13/alpha-ops",
            "text": "release gate",
            "metadata": {},
        }
    ]
    assert (
        normalize_external_rows(
            request,
            rows,
            return_citations_default=True,
        )["citations"]
        == []
    )


def test_score_threshold_filters_normalized_rows_before_ranking_and_citations() -> None:
    request = {
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "score_threshold": 0.8,
        "return_citations": True,
    }
    result = normalize_external_rows(
        request,
        [
            {
                "score": 0.79,
                "chunk_id": "chunk_below",
                "source_id": "src_ops_playbook",
                "source_title": "Below Threshold",
                "source_uri": "agentpm://examples/m13/below",
                "text": "below",
                "metadata": {},
            },
            {
                "score": 0.95,
                "chunk_id": "chunk_above",
                "source_id": "src_ops_playbook",
                "source_title": "Above Threshold",
                "source_uri": "agentpm://examples/m13/above",
                "text": "above",
                "metadata": {},
            },
        ],
    )
    assert [
        {
            "rank": row["rank"],
            "score": row["score"],
            "chunk_id": row["chunk_id"],
        }
        for row in result["results"]
    ] == [{"rank": 1, "score": 0.95, "chunk_id": "chunk_above"}]
    assert result["citations"] == [
        {
            "chunk_id": "chunk_above",
            "source_id": "src_ops_playbook",
            "title": "Above Threshold",
            "uri": "agentpm://examples/m13/above",
        }
    ]


def test_pinecone_query_body_maps_top_k_and_fixed_attestation_filters() -> None:
    assert pinecone_query_body(
        {
            "package": "@zack/m13-reference-corpus",
            "version": "0.1.0",
            "mode": "vector_query",
            "query": "alpha launch",
            "top_k": 7,
            "score_threshold": 0.8,
        },
        [0.1, 0.2, 0.3],
        CONFIG,
        "manual-namespace",
    ) == {
        "namespace": "manual-namespace",
        "vector": [0.1, 0.2, 0.3],
        "topK": 7,
        "includeMetadata": True,
        "filter": {
            "package": {"$eq": "@zack/m13-reference-corpus"},
            "version": {"$eq": "0.1.0"},
            "corpus": {"$eq": "sha256:test-corpus"},
        },
    }


def test_pgvector_query_values_map_vector_attestation_filters_and_top_k() -> None:
    assert pgvector_query_values(
        {
            "package": "@zack/m13-reference-corpus",
            "version": "0.1.0",
            "mode": "vector_query",
            "query": "alpha launch",
            "top_k": 5,
        },
        [0.1, 0.2, -0.3],
        CONFIG,
    ) == (
        "[0.1,0.2,-0.3]",
        "@zack/m13-reference-corpus",
        "0.1.0",
        "sha256:test-corpus",
        "[0.1,0.2,-0.3]",
        5,
    )


def test_pgvector_rows_normalize_to_stable_results_and_citations() -> None:
    request = {
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "return_citations": True,
    }
    assert normalize_external_rows(
        request,
        [
            {
                "score": 0.93,
                "chunk_id": "chunk_pgvector",
                "source_id": "src_pgvector",
                "source_title": "pgvector Source",
                "source_uri": "agentpm://examples/m13/pgvector",
                "text": "pgvector row",
                "metadata": {"backend": "pgvector"},
            }
        ],
    ) == {
        "ok": True,
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "results": [
            {
                "rank": 1,
                "score": 0.93,
                "chunk_id": "chunk_pgvector",
                "source_id": "src_pgvector",
                "source_title": "pgvector Source",
                "source_uri": "agentpm://examples/m13/pgvector",
                "text": "pgvector row",
                "chunk_metadata": {"backend": "pgvector"},
            }
        ],
        "citations": [
            {
                "chunk_id": "chunk_pgvector",
                "source_id": "src_pgvector",
                "title": "pgvector Source",
                "uri": "agentpm://examples/m13/pgvector",
            }
        ],
    }


def test_pgvector_sql_helpers_reject_unsafe_identifiers_and_serialize_vectors() -> None:
    assert (
        sql_identifier("agentpm_m13_knowledge_chunks") == "agentpm_m13_knowledge_chunks"
    )
    assert vector_literal([1, 0.5, -0.25]) == "[1,0.5,-0.25]"
    with pytest.raises(RuntimeError, match="unsafe SQL identifier"):
        sql_identifier("agentpm-m13")
    with pytest.raises(RuntimeError, match="unsafe SQL identifier"):
        sql_identifier("chunks;drop_table")


def test_provider_failures_use_typed_knowledge_failure_result_shape() -> None:
    assert failure_result(
        {
            "package": "@zack/m13-reference-corpus",
            "version": "0.1.0",
            "mode": "vector_query",
            "query": "alpha launch",
        },
        "pgvector_query_failed",
        "database unavailable",
    ) == {
        "ok": False,
        "package": "@zack/m13-reference-corpus",
        "version": "0.1.0",
        "mode": "vector_query",
        "query": "alpha launch",
        "error": {
            "code": "pgvector_query_failed",
            "message": "database unavailable",
            "retryable": False,
        },
    }


def test_pinecone_metadata_identity_mismatch_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="mismatched package"):
        pinecone_matches_to_rows(
            [
                {
                    "id": "chunk_release_gate",
                    "score": 0.99,
                    "metadata": {
                        "package": "@zack/other",
                        "version": "0.1.0",
                        "corpus": "sha256:test-corpus",
                    },
                }
            ],
            CONFIG,
        )


def test_python_pinecone_retrieve_returns_typed_failure_for_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pinecone_runtime, "CONFIG", CONFIG)
    monkeypatch.setattr(
        pinecone_runtime,
        "openai_embed",
        lambda _text, _config: (_ for _ in ()).throw(KeyError("missing embedding")),
    )
    result = pinecone_runtime.retrieve(
        {
            "package": "@zack/m13-reference-corpus",
            "version": "0.1.0",
            "mode": "vector_query",
            "query": "alpha launch",
        }
    )
    assert result["ok"] is False
    assert result["package"] == "@zack/m13-reference-corpus"
    assert result["version"] == "0.1.0"
    assert result["mode"] == "vector_query"
    assert result["query"] == "alpha launch"
    assert result["error"]["code"] == "pinecone_query_failed"
    assert result["error"]["retryable"] is False
    assert "missing embedding" in result["error"]["message"]


def test_python_pgvector_retrieve_returns_typed_failure_for_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pgvector_runtime, "CONFIG", CONFIG)
    monkeypatch.setenv("PGVECTOR_DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(
        pgvector_runtime,
        "openai_embed",
        lambda _text, _config: (_ for _ in ()).throw(KeyError("missing embedding")),
    )
    result = pgvector_runtime.retrieve(
        {
            "package": "@zack/m13-reference-corpus",
            "version": "0.1.0",
            "mode": "vector_query",
            "query": "alpha launch",
        }
    )
    assert result["ok"] is False
    assert result["package"] == "@zack/m13-reference-corpus"
    assert result["version"] == "0.1.0"
    assert result["mode"] == "vector_query"
    assert result["query"] == "alpha launch"
    assert result["error"]["code"] == "pgvector_query_failed"
    assert result["error"]["retryable"] is False
    assert "missing embedding" in result["error"]["message"]
