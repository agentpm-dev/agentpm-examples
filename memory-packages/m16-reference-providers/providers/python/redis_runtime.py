from __future__ import annotations

import base64
import json
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from reference_runtime import (
    content_matches_filter_path,
    durable_content_hash,
    provider_config,
    redis_capabilities,
    scope_hash,
    stable_scope_json,
    unsupported_semantic_read_result,
)

PREFIX = "agentpm:m16:memory"


class RedisMemoryStore:
    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def open(cls, redis_url: str) -> "RedisMemoryStore":
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError(
                "Install the redis extra to use redis-memory-reference"
            ) from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True))

    def handle(self, method: Any, payload: Any) -> dict[str, Any]:
        request = payload.get("request", payload) if isinstance(payload, dict) else {}
        if method == "read":
            return self.read(request)
        if method == "write":
            return self.write(request)
        if method == "count":
            return self.count(request)
        if method == "load_operation_state":
            return self.load_operation_state(request)
        if method == "store_operation_state":
            return self.store_operation_state(
                request,
                (
                    payload.get("state", request.get("state"))
                    if isinstance(payload, dict)
                    else None
                ),
            )
        if method == "commit_lifecycle":
            return self.commit_lifecycle(request)
        raise RuntimeError(f"unsupported MemoryRuntime method {method}")

    def active_records(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        scope_json = stable_scope_json(request.get("scope"))
        scope_hash_value = scope_hash(scope_json)
        ids = (
            [request["record_id"]]
            if request.get("record_id")
            else list(
                self.client.smembers(
                    active_set_key(
                        request["package"],
                        request["package_version"],
                        request["space"],
                        scope_hash_value,
                    )
                )
            )
        )
        now = datetime.fromisoformat(
            str(request.get("now") or datetime.now(UTC).isoformat()).replace(
                "Z", "+00:00"
            )
        )
        records = []
        for record_id in ids:
            record = self.read_record(record_id)
            if not record:
                continue
            expires = record.get("expires_at")
            expired = bool(
                expires
                and datetime.fromisoformat(str(expires).replace("Z", "+00:00")) <= now
            )
            if (
                record["package"] == request["package"]
                and record["package_version"] == request["package_version"]
                and record["space"] == request["space"]
                and record["scope_hash"] == scope_hash_value
                and (
                    not request.get("record_type")
                    or record["record_type"] == request["record_type"]
                )
                and not record.get("archived_at")
                and not expired
            ):
                records.append(record)
        return sort_records(records)

    def read(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("mode") == "semantic":
            return unsupported_semantic_read_result(request)
        records = self.active_records(request)
        mode = request.get("mode")
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

    def write(self, request: dict[str, Any], pipe: Any | None = None) -> dict[str, Any]:
        operation = request.get("operation")
        if operation in {"delete", "archive"}:
            return self.mutate_existing(request, operation, pipe)

        existing = self.find_existing_for_write(request)
        if operation == "update" and not existing:
            return failed_write(request, "not_found", "record not found")
        if (
            operation == "create"
            and request.get("space_model") == "document"
            and existing
        ):
            return failed_write(request, "conflict", "document already exists")

        now = request.get("now") or datetime.now(UTC).isoformat()
        record_id = (
            existing["id"]
            if existing
            else request.get("record_id") or f"mem-{uuid.uuid4()}"
        )
        scope_json = stable_scope_json(request.get("scope"))
        scope_hash_value = scope_hash(scope_json)
        ordinal = existing.get("ordinal") if existing else None
        if request.get("space_model") == "sequence" and existing is None:
            ordinal = self.allocate_ordinal(request, scope_hash_value)
        record = {
            "id": record_id,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "space_model": request["space_model"],
            "record_type": request["record_type"],
            "schema_version": request["schema_version"],
            "scope_json": scope_json,
            "scope_hash": scope_hash_value,
            "content": request.get("content") or {},
            "provenance": request.get("provenance") or {},
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "expires_at": (
                existing.get("expires_at")
                if existing
                else expires_at(request["space"], now)
            ),
            "archived_at": None,
            "ordinal": ordinal,
        }
        transaction = pipe or self.client.pipeline(transaction=True)
        queue_record_hash(transaction, record)
        transaction.sadd(
            active_set_key(
                record["package"],
                record["package_version"],
                record["space"],
                record["scope_hash"],
            ),
            record["id"],
        )
        if pipe is None:
            transaction.execute()
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

    def find_existing_for_write(self, request: dict[str, Any]) -> dict[str, Any] | None:
        if request.get("record_id"):
            return self.read_record(request["record_id"])
        if request.get("space_model") == "document":
            records = self.active_records(request)
            return records[0] if records else None
        return None

    def mutate_existing(
        self, request: dict[str, Any], operation: str, pipe: Any | None = None
    ) -> dict[str, Any]:
        records = self.active_records(request)
        transaction = pipe or self.client.pipeline(transaction=True)
        now = request.get("now") or datetime.now(UTC).isoformat()
        for record in records:
            key = active_set_key(
                record["package"],
                record["package_version"],
                record["space"],
                record["scope_hash"],
            )
            if operation == "delete":
                transaction.delete(record_key(record["id"]))
                transaction.srem(key, record["id"])
            else:
                archived = {**record, "archived_at": now, "updated_at": now}
                queue_record_hash(transaction, archived)
                transaction.srem(key, record["id"])
        if pipe is None:
            transaction.execute()
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
        raw = self.client.get(
            operation_state_key(
                request["package"],
                request["package_version"],
                request["operation"],
                request.get("scope") or {},
            )
        )
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
            "state": json.loads(raw) if raw else None,
        }

    def store_operation_state(
        self, request: dict[str, Any], state: Any, pipe: Any | None = None
    ) -> dict[str, Any]:
        transaction = pipe or self.client.pipeline(transaction=True)
        transaction.set(
            operation_state_key(
                request["package"],
                request["package_version"],
                request["operation"],
                request.get("scope") or (state or {}).get("scope") or {},
            ),
            json.dumps(state or {}),
        )
        if pipe is None:
            transaction.execute()
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
        }

    def commit_lifecycle(self, request: dict[str, Any]) -> dict[str, Any]:
        source_keys = [
            record_key(source.get("record_id") or source.get("id"))
            for source in request.get("expected_sources") or []
        ]
        for _ in range(5):
            with self.client.pipeline() as pipe:
                try:
                    if source_keys:
                        pipe.watch(*source_keys)
                    if request.get("trigger_precondition"):
                        self.validate_trigger_precondition(
                            request["trigger_precondition"], request.get("now")
                        )
                    for source in request.get("expected_sources") or []:
                        record_id = source.get("record_id") or source.get("id")
                        record = self.read_record(record_id)
                        if not record or durable_content_hash(
                            record["content"]
                        ) != source.get("content_hash"):
                            raise RuntimeError(f"stale lifecycle source {record_id}")

                    pipe.multi()
                    output_ids = []
                    source_ids = []
                    for write in request.get("output_writes") or []:
                        result = self.write(write, pipe)
                        if not result["ok"]:
                            raise RuntimeError(
                                result.get("error", {}).get(
                                    "message", "output write failed"
                                )
                            )
                        if result.get("record_id"):
                            output_ids.append(result["record_id"])
                    for write in request.get("source_mutations") or []:
                        result = self.write(write, pipe)
                        if not result["ok"]:
                            raise RuntimeError(
                                result.get("error", {}).get(
                                    "message", "source mutation failed"
                                )
                            )
                        if result.get("record_id"):
                            source_ids.append(result["record_id"])
                    operation_state = dict(request.get("operation_state") or {})
                    operation_state["watermark"] = (
                        lifecycle_watermark_with_commit_records(
                            operation_state.get("watermark"), output_ids, source_ids
                        )
                    )
                    self.store_operation_state(
                        {
                            "package": request["package"],
                            "package_version": request["package_version"],
                            "operation": request["operation"],
                            "scope": operation_state.get("scope") or {},
                        },
                        operation_state,
                        pipe,
                    )
                    pipe.execute()
                    return {
                        "ok": True,
                        "package": request["package"],
                        "package_version": request["package_version"],
                        "operation": request["operation"],
                        "output_record_ids": output_ids,
                        "source_record_ids": source_ids,
                    }
                except Exception as exc:
                    if exc.__class__.__name__ == "WatchError":
                        time.sleep(0.01)
                        continue
                    return {
                        "ok": False,
                        "package": request["package"],
                        "package_version": request["package_version"],
                        "operation": request["operation"],
                        "output_record_ids": [],
                        "source_record_ids": [],
                        "error": {"code": "commit_failed", "message": str(exc)},
                    }
        return {
            "ok": False,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
            "output_record_ids": [],
            "source_record_ids": [],
            "error": {
                "code": "commit_failed",
                "message": "Redis MemoryRuntime state changed too frequently to commit atomically",
            },
        }

    def validate_trigger_precondition(self, precondition: Any, now: str | None) -> None:
        kind, payload = normalize_precondition(precondition)
        if not payload:
            return
        count = self.count(
            {
                "package": payload["package"],
                "package_version": payload["package_version"],
                "space": payload["space"],
                "scope": payload.get("scope"),
                "now": now,
            }
        )["count"]
        if kind == "ActiveCountAtLeast" and count < payload["threshold"]:
            raise RuntimeError(
                f"active count {count} is below threshold {payload['threshold']}"
            )
        if kind == "ActiveCountAtCapacity" and count < payload["max_records"]:
            raise RuntimeError(
                f"active count {count} is below capacity {payload['max_records']}"
            )

    def read_record(self, record_id: str) -> dict[str, Any] | None:
        raw = self.client.hgetall(record_key(record_id))
        return record_from_hash(raw) if raw and raw.get("id") else None

    def allocate_ordinal(self, request: dict[str, Any], scope_hash_value: str) -> int:
        return int(
            self.client.incr(
                ordinal_key(
                    request["package"],
                    request["package_version"],
                    request["space"],
                    scope_hash_value,
                )
            )
        )


def queue_record_hash(pipe: Any, record: dict[str, Any]) -> None:
    pipe.hset(
        record_key(record["id"]),
        mapping={
            "id": record["id"],
            "package": record["package"],
            "package_version": record["package_version"],
            "space": record["space"],
            "space_model": record["space_model"],
            "record_type": record["record_type"],
            "schema_version": record["schema_version"],
            "scope_json": record["scope_json"],
            "scope_hash": record["scope_hash"],
            "content": json.dumps(record["content"]),
            "provenance": json.dumps(record["provenance"]),
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "expires_at": record.get("expires_at") or "",
            "archived_at": record.get("archived_at") or "",
            "ordinal": "" if record.get("ordinal") is None else str(record["ordinal"]),
        },
    )


def record_from_hash(raw: dict[str, str]) -> dict[str, Any]:
    return {
        "id": raw["id"],
        "package": raw["package"],
        "package_version": raw["package_version"],
        "space": raw["space"],
        "space_model": raw["space_model"],
        "record_type": raw["record_type"],
        "schema_version": raw["schema_version"],
        "scope_json": raw["scope_json"],
        "scope_hash": raw["scope_hash"],
        "content": json.loads(raw.get("content") or "{}"),
        "provenance": json.loads(raw.get("provenance") or "{}"),
        "created_at": raw["created_at"],
        "updated_at": raw["updated_at"],
        "expires_at": raw.get("expires_at") or None,
        "archived_at": raw.get("archived_at") or None,
        "ordinal": int(raw["ordinal"]) if raw.get("ordinal") else None,
    }


def sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: (
            record.get("ordinal") if record.get("ordinal") is not None else 2**63 - 1,
            record["created_at"],
            record["id"],
        ),
    )


def expires_at(space: str, now: str) -> str | None:
    days = {"current_note": 30, "notes": 30, "summaries": 90}.get(space)
    if days is None:
        return None
    return (
        datetime.fromisoformat(now.replace("Z", "+00:00")) + timedelta(days=days)
    ).isoformat()


def lifecycle_watermark_with_commit_records(
    watermark: Any, output_ids: list[str], source_ids: list[str]
) -> dict[str, Any]:
    result = dict(watermark) if isinstance(watermark, dict) else {}
    result["last_output_record_ids"] = output_ids
    result["last_mutated_source_record_ids"] = source_ids
    return result


def failed_write(request: dict[str, Any], code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "package": request["package"],
        "package_version": request["package_version"],
        "space": request["space"],
        "operation": request.get("operation"),
        "error": {"code": code, "message": message},
    }


def normalize_precondition(
    precondition: Any,
) -> tuple[str | None, dict[str, Any] | None]:
    if not isinstance(precondition, dict):
        return None, None
    for key in (
        "ActiveCountAtLeast",
        "ActiveCountAtCapacity",
        "active_count_at_least",
        "active_count_at_capacity",
    ):
        if key in precondition:
            normalized = (
                "ActiveCountAtLeast"
                if "Least" in key or key.endswith("least")
                else "ActiveCountAtCapacity"
            )
            return normalized, precondition[key]
    if precondition.get("type") == "active_count_at_least":
        return "ActiveCountAtLeast", precondition
    if precondition.get("type") == "active_count_at_capacity":
        return "ActiveCountAtCapacity", precondition
    return None, None


def active_set_key(
    package: str, version: str, space: str, scope_hash_value: str
) -> str:
    return f"{PREFIX}:active:{encode(package)}:{encode(version)}:{encode(space)}:{encode(scope_hash_value)}"


def record_key(record_id: str) -> str:
    return f"{PREFIX}:record:{encode(record_id)}"


def operation_state_key(
    package: str, version: str, operation: str, scope: dict[str, str]
) -> str:
    scope_json = stable_scope_json(scope)
    return f"{PREFIX}:operation-state:{encode(package)}:{encode(version)}:{encode(operation)}:{encode(scope_hash(scope_json))}"


def ordinal_key(package: str, version: str, space: str, scope_hash_value: str) -> str:
    return f"{PREFIX}:ordinal:{encode(package)}:{encode(version)}:{encode(space)}:{encode(scope_hash_value)}"


def encode(value: str) -> str:
    return base64.urlsafe_b64encode(str(value).encode()).decode().rstrip("=")


def main() -> None:
    from agentpm import serve_memory_runtime_process

    config = provider_config("redis-memory-reference")
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is required for redis-memory-reference")
    store = RedisMemoryStore.open(redis_url)
    serve_memory_runtime_process(
        config.runtime_id,
        store.handle,
        redis_capabilities(config),
    )


if __name__ == "__main__":
    main()
