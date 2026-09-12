from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from reference_runtime import (
    content_matches_filter_path,
    durable_content_hash,
    pgvector_capabilities,
    provider_config,
    scope_hash,
    stable_scope_json,
    unsupported_semantic_read_result,
)


class PostgresMemoryStore:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    @classmethod
    def open(cls, database_url: str) -> "PostgresMemoryStore":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "Install the pgvector extra to use pgvector-memory-reference"
            ) from exc
        connection = psycopg.connect(database_url)
        store = cls(connection)
        store.ensure_schema()
        return store

    def ensure_schema(self) -> None:
        with self.connection.transaction():
            self.connection.execute("""
                create table if not exists agentpm_memory_records (
                  id text primary key,
                  package text not null,
                  package_version text not null,
                  space text not null,
                  space_model text not null,
                  record_type text not null,
                  schema_version text not null,
                  scope_json text not null,
                  scope_hash text not null,
                  content jsonb not null,
                  provenance jsonb not null,
                  created_at timestamptz not null,
                  updated_at timestamptz not null,
                  expires_at timestamptz,
                  archived_at timestamptz,
                  ordinal bigint
                )
                """)
            self.connection.execute("""
                create index if not exists agentpm_memory_records_lookup
                on agentpm_memory_records(package, package_version, space, scope_hash, record_type, archived_at, expires_at)
                """)
            self.connection.execute("""
                create table if not exists agentpm_memory_operation_state (
                  package text not null,
                  package_version text not null,
                  operation text not null,
                  scope_hash text not null,
                  scope_json text not null,
                  state jsonb not null,
                  updated_at timestamptz not null default now(),
                  primary key(package, package_version, operation, scope_hash)
                )
                """)
            self.connection.execute("""
                create table if not exists agentpm_memory_ordinals (
                  package text not null,
                  package_version text not null,
                  space text not null,
                  scope_hash text not null,
                  next_ordinal bigint not null,
                  primary key(package, package_version, space, scope_hash)
                )
                """)

    def handle(self, method: Any, payload: Any) -> dict[str, Any]:
        request = payload.get("request", payload) if isinstance(payload, dict) else {}
        try:
            with self.connection.transaction():
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
                    response = self.commit_lifecycle(request)
                    if response.get("ok") is False:
                        raise RollbackLifecycleCommit(response)
                    return response
        except RollbackLifecycleCommit as rollback:
            return rollback.response
        raise RuntimeError(f"unsupported MemoryRuntime method {method}")

    def active_records(
        self, request: dict[str, Any], for_update: bool = False
    ) -> list[dict[str, Any]]:
        scope_json = stable_scope_json(request.get("scope"))
        lock = " for update" if for_update else ""
        rows = self.connection.execute(
            f"""
            select * from agentpm_memory_records
            where package = %s
              and package_version = %s
              and space = %s
              and scope_hash = %s
              and (%s::text is null or record_type = %s::text)
              and (%s::text is null or id = %s::text)
              and archived_at is null
              and (expires_at is null or expires_at > %s::timestamptz)
            order by ordinal nulls last, created_at asc, id asc
            {lock}
            """,
            (
                request["package"],
                request["package_version"],
                request["space"],
                scope_hash(scope_json),
                request.get("record_type"),
                request.get("record_type"),
                request.get("record_id"),
                request.get("record_id"),
                request.get("now") or datetime.now(UTC).isoformat(),
            ),
        ).fetchall()
        return [row_to_record(row) for row in rows]

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
        records = sort_records(records)
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
        self.connection.execute(
            """
            insert into agentpm_memory_records (
              id, package, package_version, space, space_model, record_type, schema_version,
              scope_json, scope_hash, content, provenance, created_at, updated_at, expires_at, archived_at, ordinal
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::timestamptz,%s::timestamptz,%s::timestamptz,%s::timestamptz,%s)
            on conflict (id) do update set
              package = excluded.package,
              package_version = excluded.package_version,
              space = excluded.space,
              space_model = excluded.space_model,
              record_type = excluded.record_type,
              schema_version = excluded.schema_version,
              scope_json = excluded.scope_json,
              scope_hash = excluded.scope_hash,
              content = excluded.content,
              provenance = excluded.provenance,
              updated_at = excluded.updated_at,
              expires_at = excluded.expires_at,
              archived_at = excluded.archived_at,
              ordinal = excluded.ordinal
            """,
            record_params(record),
        )
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
            row = self.connection.execute(
                "select * from agentpm_memory_records where id = %s for update",
                (request["record_id"],),
            ).fetchone()
            return row_to_record(row) if row else None
        if request.get("space_model") == "document":
            records = self.active_records(request, for_update=True)
            return records[0] if records else None
        return None

    def mutate_existing(
        self, request: dict[str, Any], operation: str
    ) -> dict[str, Any]:
        records = self.active_records(request, for_update=True)
        now = request.get("now") or datetime.now(UTC).isoformat()
        ids = [record["id"] for record in records]
        if ids:
            if operation == "delete":
                self.connection.execute(
                    "delete from agentpm_memory_records where id = any(%s)",
                    (ids,),
                )
            else:
                self.connection.execute(
                    "update agentpm_memory_records set archived_at = %s::timestamptz, updated_at = %s::timestamptz where id = any(%s)",
                    (now, now, ids),
                )
                for record in records:
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
        scope_json = stable_scope_json(request.get("scope"))
        row = self.connection.execute(
            """
            select count(*)::bigint
            from agentpm_memory_records
            where package = %s
              and package_version = %s
              and space = %s
              and scope_hash = %s
              and (%s::text is null or record_type = %s::text)
              and archived_at is null
              and (expires_at is null or expires_at > %s::timestamptz)
            """,
            (
                request["package"],
                request["package_version"],
                request["space"],
                scope_hash(scope_json),
                request.get("record_type"),
                request.get("record_type"),
                request.get("now") or datetime.now(UTC).isoformat(),
            ),
        ).fetchone()
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "space": request["space"],
            "count": int(row[0] if row else 0),
        }

    def load_operation_state(self, request: dict[str, Any]) -> dict[str, Any]:
        scope_json = stable_scope_json(request.get("scope"))
        row = self.connection.execute(
            """
            select state from agentpm_memory_operation_state
            where package = %s and package_version = %s and operation = %s and scope_hash = %s
            """,
            (
                request["package"],
                request["package_version"],
                request["operation"],
                scope_hash(scope_json),
            ),
        ).fetchone()
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
            "state": row[0] if row else None,
        }

    def store_operation_state(
        self, request: dict[str, Any], state: Any
    ) -> dict[str, Any]:
        state = state or {}
        scope_json = stable_scope_json(request.get("scope") or state.get("scope"))
        self.connection.execute(
            """
            insert into agentpm_memory_operation_state(package, package_version, operation, scope_hash, scope_json, state, updated_at)
            values (%s,%s,%s,%s,%s,%s::jsonb,%s::timestamptz)
            on conflict(package, package_version, operation, scope_hash) do update set
              scope_json = excluded.scope_json,
              state = excluded.state,
              updated_at = excluded.updated_at
            """,
            (
                request["package"],
                request["package_version"],
                request["operation"],
                scope_hash(scope_json),
                scope_json,
                json.dumps(state),
                state.get("updated_at")
                or request.get("now")
                or datetime.now(UTC).isoformat(),
            ),
        )
        return {
            "ok": True,
            "package": request["package"],
            "package_version": request["package_version"],
            "operation": request["operation"],
        }

    def commit_lifecycle(self, request: dict[str, Any]) -> dict[str, Any]:
        try:
            if request.get("trigger_precondition"):
                self.validate_trigger_precondition(
                    request["trigger_precondition"], request.get("now")
                )
            for source in request.get("expected_sources") or []:
                record_id = source.get("record_id") or source.get("id")
                row = self.connection.execute(
                    "select * from agentpm_memory_records where id = %s for update",
                    (record_id,),
                ).fetchone()
                record = row_to_record(row) if row else None
                if not record or durable_content_hash(record["content"]) != source.get(
                    "content_hash"
                ):
                    raise RuntimeError(f"stale lifecycle source {record_id}")

            output_ids = []
            source_ids = []
            for write in request.get("output_writes") or []:
                result = self.write(write)
                if not result["ok"]:
                    raise RuntimeError(
                        result.get("error", {}).get("message", "output write failed")
                    )
                if result.get("record_id"):
                    output_ids.append(result["record_id"])
            for write in request.get("source_mutations") or []:
                result = self.write(write)
                if not result["ok"]:
                    raise RuntimeError(
                        result.get("error", {}).get("message", "source mutation failed")
                    )
                if result.get("record_id"):
                    source_ids.append(result["record_id"])

            operation_state = dict(request.get("operation_state") or {})
            operation_state["watermark"] = lifecycle_watermark_with_commit_records(
                operation_state.get("watermark"), output_ids, source_ids
            )
            self.store_operation_state(
                {
                    "package": request["package"],
                    "package_version": request["package_version"],
                    "operation": request["operation"],
                    "scope": operation_state.get("scope") or {},
                    "now": request.get("now"),
                },
                operation_state,
            )
            return {
                "ok": True,
                "package": request["package"],
                "package_version": request["package_version"],
                "operation": request["operation"],
                "output_record_ids": output_ids,
                "source_record_ids": source_ids,
            }
        except Exception as exc:
            return {
                "ok": False,
                "package": request["package"],
                "package_version": request["package_version"],
                "operation": request["operation"],
                "output_record_ids": [],
                "source_record_ids": [],
                "error": {"code": "commit_failed", "message": str(exc)},
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

    def allocate_ordinal(self, request: dict[str, Any], scope_hash_value: str) -> int:
        row = self.connection.execute(
            """
            insert into agentpm_memory_ordinals(package, package_version, space, scope_hash, next_ordinal)
            values (%s,%s,%s,%s,1)
            on conflict(package, package_version, space, scope_hash) do update set
              next_ordinal = agentpm_memory_ordinals.next_ordinal + 1
            returning next_ordinal
            """,
            (
                request["package"],
                request["package_version"],
                request["space"],
                scope_hash_value,
            ),
        ).fetchone()
        return int(row[0])


def row_to_record(row: Any) -> dict[str, Any]:
    return {
        "id": row[0],
        "package": row[1],
        "package_version": row[2],
        "space": row[3],
        "space_model": row[4],
        "record_type": row[5],
        "schema_version": row[6],
        "scope_json": row[7],
        "scope_hash": row[8],
        "content": row[9] or {},
        "provenance": row[10] or {},
        "created_at": iso(row[11]),
        "updated_at": iso(row[12]),
        "expires_at": iso(row[13]) if row[13] else None,
        "archived_at": iso(row[14]) if row[14] else None,
        "ordinal": int(row[15]) if row[15] is not None else None,
    }


class RollbackLifecycleCommit(Exception):
    def __init__(self, response: dict[str, Any]) -> None:
        super().__init__(response.get("error", {}).get("message", "commit failed"))
        self.response = response


def record_params(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["id"],
        record["package"],
        record["package_version"],
        record["space"],
        record["space_model"],
        record["record_type"],
        record["schema_version"],
        record["scope_json"],
        record["scope_hash"],
        json.dumps(record["content"]),
        json.dumps(record["provenance"]),
        record["created_at"],
        record["updated_at"],
        record["expires_at"],
        record["archived_at"],
        record["ordinal"],
    )


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


def iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return (
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        .astimezone(UTC)
        .isoformat()
    )


def main() -> None:
    from agentpm import serve_memory_runtime_process

    config = provider_config("pgvector-memory-reference")
    database_url = os.environ.get("PGVECTOR_DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "PGVECTOR_DATABASE_URL is required for pgvector-memory-reference"
        )
    store = PostgresMemoryStore.open(database_url)
    serve_memory_runtime_process(
        config.runtime_id,
        store.handle,
        pgvector_capabilities(config),
    )


if __name__ == "__main__":
    main()
