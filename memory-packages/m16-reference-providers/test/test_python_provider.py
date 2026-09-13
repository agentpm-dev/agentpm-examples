from __future__ import annotations

from typing import Any

import pytest

from reference_runtime import (
    ProviderConfig,
    ReferenceMemoryStore,
    durable_content_hash,
    pgvector_capabilities,
    provider_config,
    redis_capabilities,
)

BASE_REQUEST: dict[str, Any] = {
    "package": "@zack/m16-reference-memory",
    "package_version": "0.1.0",
    "space": "notes",
    "space_model": "collection",
    "record_type": "note",
    "schema_version": "1.0.0",
    "scope": {"user": "m16-user"},
    "provenance": {"harness": {"kind": "test"}},
    "now": "2026-09-11T00:00:00Z",
}


def test_pgvector_capabilities_omit_semantic_and_reject_unfinished_flag() -> None:
    config = provider_config("pgvector-memory-reference")
    assert pgvector_capabilities(config)["descriptor"] == {
        "space_models": ["document", "collection", "sequence"],
        "retrieval_modes": ["key", "filter", "chronological", "full_text"],
        "retention_actions": ["delete", "archive"],
        "constraints": ["append_only"],
        "capacity": True,
        "durable_trigger_state": True,
        "atomic_batches": True,
    }
    with pytest.raises(RuntimeError, match="semantic retrieval is not implemented"):
        pgvector_capabilities(
            ProviderConfig(
                runtime_id="pgvector-memory-reference",
                package_name="pkg",
                version="0.1.0",
                pgvector_semantic=True,
                redis_semantic=False,
            )
        )


def test_redis_capabilities_omit_semantic_and_reject_unfinished_flag() -> None:
    config = provider_config("redis-memory-reference")
    capabilities = redis_capabilities(config)
    assert capabilities["descriptor"]["retrieval_modes"] == [
        "key",
        "filter",
        "chronological",
        "full_text",
    ]
    assert capabilities["descriptor"]["durable_trigger_state"] is True
    assert capabilities["descriptor"]["atomic_batches"] is False
    with pytest.raises(RuntimeError, match="semantic retrieval is not implemented"):
        redis_capabilities(
            ProviderConfig(
                runtime_id="redis-memory-reference",
                package_name="pkg",
                version="0.1.0",
                pgvector_semantic=False,
                redis_semantic=True,
            )
        )


def test_provider_config_rejects_semantic_env_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENTPM_MEMORY_PGVECTOR_SEMANTIC", "true")
    with pytest.raises(RuntimeError, match="AGENTPM_MEMORY_PGVECTOR_SEMANTIC=true"):
        provider_config("pgvector-memory-reference")

    monkeypatch.delenv("AGENTPM_MEMORY_PGVECTOR_SEMANTIC")
    monkeypatch.setenv("AGENTPM_MEMORY_REDIS_STACK", "true")
    with pytest.raises(RuntimeError, match="AGENTPM_MEMORY_REDIS_STACK=true"):
        provider_config("redis-memory-reference")


def test_store_handles_direct_write_read_count_and_state() -> None:
    store = ReferenceMemoryStore()
    write = store.handle(
        "write",
        {
            "request": {
                **BASE_REQUEST,
                "operation": "create",
                "content": {"body": "alpha note", "topic": "launch"},
            }
        },
    )
    assert write["ok"] is True
    assert write["record_id"].startswith("mem-")

    read = store.handle(
        "read",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "space": BASE_REQUEST["space"],
                "scope": BASE_REQUEST["scope"],
                "mode": "filter",
                "record_type": "note",
                "filter": {"topic": "launch"},
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert read["count"] == 1
    assert read["records"][0]["content"]["body"] == "alpha note"
    assert_filter_conformance(store)

    semantic_read = store.handle(
        "read",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "space": BASE_REQUEST["space"],
                "scope": BASE_REQUEST["scope"],
                "mode": "semantic",
                "record_type": "note",
                "query": "launch",
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert semantic_read["ok"] is False
    assert semantic_read["error"]["code"] == "unsupported_capability"
    assert semantic_read["embedding_requests"] == 0

    count = store.handle(
        "count",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "space": BASE_REQUEST["space"],
                "scope": BASE_REQUEST["scope"],
                "record_type": "note",
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert count["count"] == 1

    store.handle(
        "store_operation_state",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "operation": "summarize_notes",
                "scope": BASE_REQUEST["scope"],
                "now": BASE_REQUEST["now"],
            },
            "state": {"armed": True, "trigger_type": "record_count"},
        },
    )
    state = store.handle(
        "load_operation_state",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "operation": "summarize_notes",
                "scope": BASE_REQUEST["scope"],
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert state["state"] == {"armed": True, "trigger_type": "record_count"}


def test_lifecycle_commit_writes_outputs_mutates_sources_and_rolls_back_stale() -> None:
    store = ReferenceMemoryStore()
    source = store.handle(
        "write",
        {
            "request": {
                **BASE_REQUEST,
                "operation": "create",
                "content": {"body": "source note", "topic": "ops"},
            }
        },
    )
    output_write = {
        **BASE_REQUEST,
        "space": "summaries",
        "record_type": "summary",
        "operation": "create",
        "content": {"summary": "source note", "source_count": 1},
    }
    delete_source = {
        **BASE_REQUEST,
        "operation": "delete",
        "record_id": source["record_id"],
    }
    commit = store.handle(
        "commit_lifecycle",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "operation": "summarize_notes",
                "expected_sources": [
                    {
                        "id": source["record_id"],
                        "content_hash": durable_content_hash(
                            source["record"]["content"]
                        ),
                    }
                ],
                "output_writes": [output_write],
                "source_mutations": [delete_source],
                "operation_state": {
                    "package": BASE_REQUEST["package"],
                    "package_version": BASE_REQUEST["package_version"],
                    "operation": "summarize_notes",
                    "scope": BASE_REQUEST["scope"],
                    "trigger_type": "record_count",
                    "armed": True,
                    "updated_at": BASE_REQUEST["now"],
                },
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert commit["ok"] is True
    assert len(commit["output_record_ids"]) == 1
    assert commit["source_record_ids"] == [source["record_id"]]

    stale = store.handle(
        "commit_lifecycle",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "operation": "summarize_notes",
                "expected_sources": [
                    {"id": source["record_id"], "content_hash": "sha256:stale"}
                ],
                "output_writes": [output_write],
                "source_mutations": [],
                "operation_state": {"scope": BASE_REQUEST["scope"]},
                "now": BASE_REQUEST["now"],
            }
        },
    )
    assert stale["ok"] is False
    assert stale["error"]["code"] == "commit_failed"


def assert_filter_conformance(store: ReferenceMemoryStore) -> None:
    scope = {"user": "m16-python-filter"}
    now = "2026-09-11T00:01:00Z"
    base = {
        **BASE_REQUEST,
        "scope": scope,
        "now": now,
        "provenance": {"harness": {"kind": "filter-conformance-test"}},
    }
    store.handle(
        "write",
        {
            "request": {
                **base,
                "operation": "create",
                "content": {
                    "marker": "python-filter-match",
                    "topic": "launch",
                    "status": "ready",
                    "tags": ["alpha", "beta"],
                    "nested": {"level": {"value": "deep"}},
                    "members": [{"name": "no"}, {"name": "target"}],
                    "groups": [{"items": [{"name": "x"}]}],
                    "arrayValue": [{"code": "a"}, {"code": "b"}],
                    "a": {"b": 1},
                    "presentNull": None,
                },
            }
        },
    )
    store.handle(
        "write",
        {
            "request": {
                **base,
                "operation": "create",
                "content": {
                    "marker": "python-filter-other",
                    "topic": "other",
                    "status": "draft",
                    "tags": ["gamma"],
                    "nested": {"level": {"value": "shallow"}},
                    "members": [{"name": "other"}],
                    "groups": [{"items": [{"name": "y"}]}],
                    "arrayValue": [{"code": "z"}],
                    "a": {"b": 1},
                },
            }
        },
    )

    assert_filter_markers(store, scope, {"topic": "launch"}, ["python-filter-match"])
    assert_filter_markers(store, scope, {"tags": "beta"}, ["python-filter-match"])
    assert_filter_markers(
        store, scope, {"nested.level.value": "deep"}, ["python-filter-match"]
    )
    assert_filter_markers(
        store, scope, {"members.name": "target"}, ["python-filter-match"]
    )
    assert_filter_markers(
        store, scope, {"groups.items.name": "x"}, ["python-filter-match"]
    )
    assert_filter_markers(store, scope, {"presentNull": None}, ["python-filter-match"])
    assert_filter_markers(store, scope, {"a.c": None}, [])
    assert_filter_markers(
        store,
        scope,
        {"arrayValue": [{"code": "a"}, {"code": "b"}]},
        ["python-filter-match"],
    )
    assert_filter_markers(
        store, scope, {"topic": "launch", "status": "ready"}, ["python-filter-match"]
    )
    assert_filter_markers(store, scope, {"topic": "missing"}, [])


def assert_filter_markers(
    store: ReferenceMemoryStore,
    scope: dict[str, str],
    filter_value: dict[str, Any],
    expected_markers: list[str],
) -> None:
    read = store.handle(
        "read",
        {
            "request": {
                "package": BASE_REQUEST["package"],
                "package_version": BASE_REQUEST["package_version"],
                "space": BASE_REQUEST["space"],
                "scope": scope,
                "mode": "filter",
                "record_type": "note",
                "filter": filter_value,
                "now": "2026-09-11T00:01:00Z",
            }
        },
    )
    assert sorted(record["content"]["marker"] for record in read["records"]) == sorted(
        expected_markers
    )
