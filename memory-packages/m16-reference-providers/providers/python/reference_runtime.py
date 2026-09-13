from __future__ import annotations

import hashlib
import json
import os
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ProviderConfig:
    runtime_id: str
    package_name: str
    version: str
    pgvector_semantic: bool
    redis_semantic: bool


def provider_config(default_runtime_id: str) -> ProviderConfig:
    pgvector_semantic = os.environ.get("AGENTPM_MEMORY_PGVECTOR_SEMANTIC") == "true"
    redis_semantic = os.environ.get("AGENTPM_MEMORY_REDIS_STACK") == "true"
    if pgvector_semantic:
        raise RuntimeError(
            "AGENTPM_MEMORY_PGVECTOR_SEMANTIC=true is not supported yet; "
            "semantic retrieval requires real pgvector embedding storage and ranking."
        )
    if redis_semantic:
        raise RuntimeError(
            "AGENTPM_MEMORY_REDIS_STACK=true is not supported yet; "
            "semantic retrieval requires real Redis Stack vector storage and ranking."
        )
    return ProviderConfig(
        runtime_id=os.environ.get("AGENTPM_MEMORY_RUNTIME_ID", default_runtime_id),
        package_name=os.environ.get(
            "AGENTPM_MEMORY_PACKAGE", "@zack/m16-reference-memory"
        ),
        version=os.environ.get("AGENTPM_MEMORY_VERSION", "0.1.0"),
        pgvector_semantic=pgvector_semantic,
        redis_semantic=redis_semantic,
    )


def pgvector_capabilities(config: ProviderConfig) -> dict[str, Any]:
    if config.pgvector_semantic:
        raise RuntimeError(
            "semantic retrieval is not implemented by the M16 pgvector reference provider"
        )
    return {
        "descriptor": {
            "space_models": ["document", "collection", "sequence"],
            "retrieval_modes": ["key", "filter", "chronological", "full_text"],
            "retention_actions": ["delete", "archive"],
            "constraints": ["append_only"],
            "capacity": True,
            "durable_trigger_state": True,
            "atomic_batches": True,
        },
        "packages": [
            {"package": config.package_name, "version": config.version, "ready": True}
        ],
    }


def redis_capabilities(config: ProviderConfig) -> dict[str, Any]:
    if config.redis_semantic:
        raise RuntimeError(
            "semantic retrieval is not implemented by the M16 Redis reference provider"
        )
    return {
        "descriptor": {
            "space_models": ["document", "collection", "sequence"],
            "retrieval_modes": ["key", "filter", "chronological", "full_text"],
            "retention_actions": ["delete", "archive"],
            "constraints": ["append_only"],
            "capacity": True,
            "durable_trigger_state": True,
            "atomic_batches": False,
        },
        "packages": [
            {"package": config.package_name, "version": config.version, "ready": True}
        ],
    }


def stable_scope_json(scope: dict[str, str] | None) -> str:
    return json.dumps(dict(sorted((scope or {}).items())), separators=(",", ":"))


def scope_hash(scope_json: str) -> str:
    return "sha256:" + hashlib.sha256(scope_json.encode("utf-8")).hexdigest()


def durable_content_hash(content: Any) -> str:
    encoded = json.dumps(content or {}, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def unwrap_request(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("request"), dict):
        return payload["request"]
    return payload if isinstance(payload, dict) else {}


def content_matches_filter_path(
    value: Any, path: str | list[str], expected: Any
) -> bool:
    segments = path if isinstance(path, list) else str(path).split(".")
    if not segments and value == expected:
        return True
    if isinstance(value, list):
        return any(
            content_matches_filter_path(item, segments, expected) for item in value
        )
    if isinstance(value, dict) and segments:
        head = segments[0]
        return head in value and content_matches_filter_path(
            value[head], segments[1:], expected
        )
    return False


def unsupported_semantic_read_result(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "package": request["package"],
        "package_version": request["package_version"],
        "space": request["space"],
        "mode": request.get("mode"),
        "records": [],
        "count": 0,
        "embedding_requests": 0,
        "vectors_materialized": 0,
        "vectors_pending": 0,
        "error": {
            "code": "unsupported_capability",
            "message": "semantic retrieval is not implemented by the M16 reference providers",
        },
    }


class ReferenceMemoryStore:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.operation_states: dict[str, dict[str, Any]] = {}
        self.next_ordinals: dict[str, int] = {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "operation_states": self.operation_states,
            "next_ordinals": self.next_ordinals,
        }

    def restore(self, snapshot: dict[str, Any] | None) -> None:
        snapshot = snapshot or {}
        self.records = dict(snapshot.get("records") or {})
        self.operation_states = dict(snapshot.get("operation_states") or {})
        self.next_ordinals = dict(snapshot.get("next_ordinals") or {})

    def handle(self, method: str, payload: Any) -> dict[str, Any]:
        request = unwrap_request(payload)
        if method == "read":
            return self.read(request)
        if method == "write":
            return self.write(request)
        if method == "count":
            return self.count(request)
        if method == "load_operation_state":
            return self.load_operation_state(request)
        if method == "store_operation_state":
            state = (
                payload.get("state")
                if isinstance(payload, dict)
                else request.get("state")
            )
            return self.store_operation_state(request, state)
        if method == "commit_lifecycle":
            return self.commit_lifecycle(request)
        raise RuntimeError(f"unsupported MemoryRuntime method {method}")

    def active_records(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        scope_json = stable_scope_json(request.get("scope"))
        now = datetime.fromisoformat(
            str(request.get("now") or datetime.now(UTC).isoformat()).replace(
                "Z", "+00:00"
            )
        )
        records = []
        for record in self.records.values():
            expires_at = record.get("expires_at")
            expired = bool(
                expires_at
                and datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                <= now
            )
            if (
                record["package"] == request.get("package")
                and record["package_version"] == request.get("package_version")
                and record["space"] == request.get("space")
                and record["scope_json"] == scope_json
                and (
                    not request.get("record_type")
                    or record["record_type"] == request.get("record_type")
                )
                and not record.get("archived_at")
                and not expired
            ):
                records.append(record)
        return records

    def read(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("mode") == "semantic":
            return unsupported_semantic_read_result(request)
        records = self.active_records(request)
        mode = request.get("mode")
        if mode == "key" and request.get("record_id"):
            records = [
                record for record in records if record["id"] == request["record_id"]
            ]
        if mode == "filter":
            for path, expected in (request.get("filter") or {}).items():
                records = [
                    record
                    for record in records
                    if content_matches_filter_path(record["content"], path, expected)
                ]
        if mode == "full_text" and request.get("query"):
            query = str(request["query"]).lower()
            records = [
                record
                for record in records
                if query in json.dumps(record["content"]).lower()
            ]
        records = sorted(
            records,
            key=lambda record: (
                (
                    record.get("ordinal")
                    if record.get("ordinal") is not None
                    else 2**63 - 1
                ),
                record["created_at"],
                record["id"],
            ),
        )
        if request.get("limit"):
            records = records[: int(request["limit"])]
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "mode": mode,
            "records": records,
            "count": len(records),
            "embedding_requests": 0,
            "vectors_materialized": 0,
            "vectors_pending": 0,
        }

    def write(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = request.get("operation")
        if operation in {"delete", "archive"}:
            return self.mutate_existing(request, operation)
        existing = None
        if request.get("record_id"):
            existing = self.records.get(request["record_id"])
        if not existing and request.get("space_model") == "document":
            active = self.active_records(request)
            existing = active[0] if active else None
        if operation == "update" and not existing:
            return self.failed_write(request, "not_found", "record not found")
        if (
            operation == "create"
            and request.get("space_model") == "document"
            and existing
        ):
            return self.failed_write(request, "conflict", "document already exists")

        now = request.get("now") or datetime.now(UTC).isoformat()
        record_id = (
            existing["id"]
            if existing
            else request.get("record_id") or f"mem-{uuid.uuid4()}"
        )
        scope_json = stable_scope_json(request.get("scope"))
        ordinal = existing.get("ordinal") if existing else None
        if request.get("space_model") == "sequence" and existing is None:
            ordinal = self.allocate_ordinal(request, scope_json)
        record = {
            "id": record_id,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "space_model": request["space_model"],
            "record_type": request["record_type"],
            "schema_version": request["schema_version"],
            "scope_json": scope_json,
            "scope_hash": scope_hash(scope_json),
            "content": request.get("content") or {},
            "provenance": request.get("provenance") or {},
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "expires_at": existing.get("expires_at") if existing else None,
            "archived_at": None,
            "ordinal": ordinal,
        }
        self.records[record_id] = record
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "operation": operation,
            "record_id": record_id,
            "record": record,
            "embedding_requests": 0,
        }

    def mutate_existing(
        self, request: dict[str, Any], operation: str
    ) -> dict[str, Any]:
        records = (
            [self.records[request["record_id"]]]
            if request.get("record_id") in self.records
            else self.active_records(request)
        )
        now = request.get("now") or datetime.now(UTC).isoformat()
        for record in records:
            if operation == "delete":
                self.records.pop(record["id"], None)
            else:
                record["archived_at"] = now
                record["updated_at"] = now
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "operation": operation,
            "record_id": records[0]["id"] if records else None,
            "record": records[0] if records else None,
            "embedding_requests": 0,
        }

    def count(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "count": len(self.active_records(request)),
        }

    def load_operation_state(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
            "state": self.operation_states.get(self.state_key(request)),
        }

    def store_operation_state(
        self, request: dict[str, Any], state: Any
    ) -> dict[str, Any]:
        self.operation_states[self.state_key(request)] = state
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
        }

    def commit_lifecycle(self, request: dict[str, Any]) -> dict[str, Any]:
        records = deepcopy(self.records)
        states = deepcopy(self.operation_states)
        try:
            for source in request.get("expected_sources") or []:
                record = self.records.get(source["id"])
                if (
                    not record
                    or durable_content_hash(record["content"]) != source["content_hash"]
                ):
                    raise RuntimeError(f"stale lifecycle source {source['id']}")
            output_ids = []
            source_ids = []
            for write in request.get("output_writes") or []:
                result = self.write(write)
                if not result["ok"]:
                    raise RuntimeError(
                        result.get("error", {}).get("message", "output write failed")
                    )
                output_ids.append(result["record_id"])
            for write in request.get("source_mutations") or []:
                result = self.write(write)
                if not result["ok"]:
                    raise RuntimeError(
                        result.get("error", {}).get("message", "source mutation failed")
                    )
                if result.get("record_id"):
                    source_ids.append(result["record_id"])
            operation_state = request.get("operation_state") or {}
            self.operation_states[
                self.state_key(
                    {
                        "package": request["package"],
                        "package_version": request["package_version"],
                        "operation": request["operation"],
                        "scope": operation_state.get("scope") or {},
                    }
                )
            ] = operation_state
            return {
                "ok": True,
                "package": request["package"],
                "package_version": request["package_version"],
                "operation": request["operation"],
                "output_record_ids": output_ids,
                "source_record_ids": source_ids,
            }
        except Exception as exc:
            self.records = records
            self.operation_states = states
            return {
                "ok": False,
                "package": request["package"],
                "package_version": request["package_version"],
                "operation": request["operation"],
                "output_record_ids": [],
                "source_record_ids": [],
                "error": {"code": "commit_failed", "message": str(exc)},
            }

    def allocate_ordinal(self, request: dict[str, Any], scope_json: str) -> int:
        key = "\0".join(
            [
                request["package"],
                request["package_version"],
                request["space"],
                scope_json,
            ]
        )
        self.next_ordinals[key] = self.next_ordinals.get(key, 0) + 1
        return self.next_ordinals[key]

    def state_key(self, request: dict[str, Any]) -> str:
        return "\0".join(
            [
                request["package"],
                request["package_version"],
                request["operation"],
                stable_scope_json(request.get("scope")),
            ]
        )

    def failed_write(
        self, request: dict[str, Any], code: str, message: str
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "operation": request["operation"],
            "error": {"code": code, "message": message},
        }
