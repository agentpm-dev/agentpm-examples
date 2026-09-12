import { randomUUID } from "node:crypto";
import pg from "pg";
import { serveMemoryRuntimeProcess } from "@agentpm/sdk";
import {
  contentMatchesFilterPath,
  durableContentHash,
  lifecycleWatermarkWithCommitRecords,
  pgvectorCapabilities,
  providerConfig,
  referenceExpiresAt,
  scopeHash,
  sortMemoryRecords,
  stableScopeJson,
  unsupportedSemanticReadResult,
  unwrapRequest,
} from "./lib.mjs";

class PostgresMemoryStore {
  constructor(pool) {
    this.pool = pool;
  }

  static async open(databaseUrl) {
    const pool = new pg.Pool({ connectionString: databaseUrl });
    const store = new PostgresMemoryStore(pool);
    await store.ensureSchema();
    return store;
  }

  async close() {
    await this.pool.end();
  }

  async ensureSchema() {
    await this.pool.query(`
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
    `);
    await this.pool.query(`
      create index if not exists agentpm_memory_records_lookup
      on agentpm_memory_records(package, package_version, space, scope_hash, record_type, archived_at, expires_at)
    `);
    await this.pool.query(`
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
    `);
    await this.pool.query(`
      create table if not exists agentpm_memory_ordinals (
        package text not null,
        package_version text not null,
        space text not null,
        scope_hash text not null,
        next_ordinal bigint not null,
        primary key(package, package_version, space, scope_hash)
      )
    `);
  }

  async handle(method, payload) {
    const request = unwrapRequest(payload);
    const client = await this.pool.connect();
    try {
      await client.query("begin");
      let response;
      switch (method) {
        case "read":
          response = await this.read(client, request);
          break;
        case "write":
          response = await this.write(client, request);
          break;
        case "count":
          response = await this.count(client, request);
          break;
        case "load_operation_state":
          response = await this.loadOperationState(client, request);
          break;
        case "store_operation_state":
          response = await this.storeOperationState(client, request, payload?.state ?? request.state);
          break;
        case "commit_lifecycle":
          response = await this.commitLifecycle(client, request);
          break;
        default:
          throw new Error(`unsupported MemoryRuntime method ${method}`);
      }
      if (method === "commit_lifecycle" && response?.ok === false) {
        await client.query("rollback");
        return response;
      }
      await client.query("commit");
      return response;
    } catch (error) {
      await client.query("rollback").catch(() => undefined);
      throw error;
    } finally {
      client.release();
    }
  }

  async activeRecords(client, request, options = {}) {
    const scopeJson = stableScopeJson(request.scope || {});
    const result = await client.query(
      `
      select * from agentpm_memory_records
      where package = $1
        and package_version = $2
        and space = $3
        and scope_hash = $4
        and ($5::text is null or record_type = $5)
        and ($6::text is null or id = $6)
        and archived_at is null
        and (expires_at is null or expires_at > $7::timestamptz)
      order by ordinal nulls last, created_at asc, id asc
      ${options.forUpdate ? "for update" : ""}
      `,
      [
        request.package,
        request.package_version,
        request.space,
        scopeHash(scopeJson),
        request.record_type || null,
        request.record_id || null,
        request.now || new Date().toISOString(),
      ],
    );
    return result.rows.map(rowToRecord);
  }

  async read(client, request) {
    if (request.mode === "semantic") {
      return unsupportedSemanticReadResult(request);
    }
    let records = await this.activeRecords(client, request);
    if (request.mode === "filter") {
      for (const [path, expected] of Object.entries(request.filter || {})) {
        records = records.filter((record) => contentMatchesFilterPath(record.content, path, expected));
      }
    }
    if (request.mode === "full_text" && request.query) {
      const query = String(request.query).toLowerCase();
      records = records.filter((record) => JSON.stringify(record.content).toLowerCase().includes(query));
    }
    records = sortMemoryRecords(records);
    if (request.limit) records = records.slice(0, request.limit);
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      mode: request.mode,
      records,
      count: records.length,
      embedding_requests: 0,
      vectors_materialized: 0,
      vectors_pending: 0,
    };
  }

  async write(client, request) {
    const operation = request.operation;
    if (operation === "delete" || operation === "archive") {
      return this.mutateExisting(client, request, operation);
    }

    const existing = await this.findExistingForWrite(client, request);
    if (operation === "update" && !existing) {
      return failedWrite(request, "not_found", "record not found");
    }
    if (operation === "create" && request.space_model === "document" && existing) {
      return failedWrite(request, "conflict", "document already exists");
    }

    const now = request.now || new Date().toISOString();
    const id = existing?.id || request.record_id || `mem-${randomUUID()}`;
    const scopeJson = stableScopeJson(request.scope || {});
    const scopeHashValue = scopeHash(scopeJson);
    const ordinal =
      request.space_model === "sequence" && !existing
        ? await this.allocateOrdinal(client, request, scopeHashValue)
        : existing?.ordinal ?? null;
    const record = {
      id,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      space_model: request.space_model,
      record_type: request.record_type,
      schema_version: request.schema_version,
      scope_json: scopeJson,
      scope_hash: scopeHashValue,
      content: request.content ?? {},
      provenance: request.provenance ?? {},
      created_at: existing?.created_at || now,
      updated_at: now,
      expires_at: existing?.expires_at || referenceExpiresAt(request.space, now),
      archived_at: null,
      ordinal,
    };
    await client.query(
      `
      insert into agentpm_memory_records (
        id, package, package_version, space, space_model, record_type, schema_version,
        scope_json, scope_hash, content, provenance, created_at, updated_at, expires_at, archived_at, ordinal
      ) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb,$12::timestamptz,$13::timestamptz,$14::timestamptz,$15::timestamptz,$16)
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
      `,
      recordParams(record),
    );
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      operation,
      record_id: id,
      record,
      embedding_requests: 0,
    };
  }

  async findExistingForWrite(client, request) {
    if (request.record_id) {
      const result = await client.query("select * from agentpm_memory_records where id = $1 for update", [
        request.record_id,
      ]);
      return result.rows[0] ? rowToRecord(result.rows[0]) : undefined;
    }
    if (request.space_model === "document") {
      return (await this.activeRecords(client, request, { forUpdate: true }))[0];
    }
    return undefined;
  }

  async mutateExisting(client, request, operation) {
    const records = await this.activeRecords(client, request, { forUpdate: true });
    const now = request.now || new Date().toISOString();
    if (operation === "delete") {
      await client.query("delete from agentpm_memory_records where id = any($1::text[])", [
        records.map((record) => record.id),
      ]);
    } else {
      await client.query(
        "update agentpm_memory_records set archived_at = $1::timestamptz, updated_at = $1::timestamptz where id = any($2::text[])",
        [now, records.map((record) => record.id)],
      );
      for (const record of records) {
        record.archived_at = now;
        record.updated_at = now;
      }
    }
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      operation,
      record_id: records[0]?.id,
      record: records[0],
      embedding_requests: 0,
    };
  }

  async count(client, request) {
    const scopeJson = stableScopeJson(request.scope || {});
    const result = await client.query(
      `
      select count(*)::bigint as count
      from agentpm_memory_records
      where package = $1
        and package_version = $2
        and space = $3
        and scope_hash = $4
        and ($5::text is null or record_type = $5)
        and archived_at is null
        and (expires_at is null or expires_at > $6::timestamptz)
      `,
      [
        request.package,
        request.package_version,
        request.space,
        scopeHash(scopeJson),
        request.record_type || null,
        request.now || new Date().toISOString(),
      ],
    );
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      count: Number(result.rows[0]?.count || 0),
    };
  }

  async loadOperationState(client, request) {
    const scopeJson = stableScopeJson(request.scope || {});
    const result = await client.query(
      `
      select state from agentpm_memory_operation_state
      where package = $1 and package_version = $2 and operation = $3 and scope_hash = $4
      `,
      [request.package, request.package_version, request.operation, scopeHash(scopeJson)],
    );
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
      state: result.rows[0]?.state || null,
    };
  }

  async storeOperationState(client, request, state) {
    const scopeJson = stableScopeJson(request.scope || state?.scope || {});
    await client.query(
      `
      insert into agentpm_memory_operation_state(package, package_version, operation, scope_hash, scope_json, state, updated_at)
      values ($1,$2,$3,$4,$5,$6::jsonb,$7::timestamptz)
      on conflict(package, package_version, operation, scope_hash) do update set
        scope_json = excluded.scope_json,
        state = excluded.state,
        updated_at = excluded.updated_at
      `,
      [
        request.package,
        request.package_version,
        request.operation,
        scopeHash(scopeJson),
        scopeJson,
        JSON.stringify(state || {}),
        state?.updated_at || request.now || new Date().toISOString(),
      ],
    );
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
    };
  }

  async commitLifecycle(client, request) {
    try {
      if (request.trigger_precondition) {
        await this.validateTriggerPrecondition(client, request.trigger_precondition, request.now);
      }
      for (const source of request.expected_sources || []) {
        const recordId = source.record_id || source.id;
        const result = await client.query("select * from agentpm_memory_records where id = $1 for update", [
          recordId,
        ]);
        const record = result.rows[0] ? rowToRecord(result.rows[0]) : undefined;
        if (!record || durableContentHash(record.content) !== source.content_hash) {
          throw new Error(`stale lifecycle source ${recordId}`);
        }
      }

      const outputRecordIds = [];
      const sourceRecordIds = [];
      for (const write of request.output_writes || []) {
        const result = await this.write(client, write);
        if (!result.ok) throw new Error(result.error?.message || "output write failed");
        if (result.record_id) outputRecordIds.push(result.record_id);
      }
      for (const write of request.source_mutations || []) {
        const result = await this.write(client, write);
        if (!result.ok) throw new Error(result.error?.message || "source mutation failed");
        if (result.record_id) sourceRecordIds.push(result.record_id);
      }

      const operationState = {
        ...(request.operation_state || {}),
        watermark: lifecycleWatermarkWithCommitRecords(
          request.operation_state?.watermark,
          outputRecordIds,
          sourceRecordIds,
        ),
      };
      await this.storeOperationState(
        client,
        {
          package: request.package,
          package_version: request.package_version,
          operation: request.operation,
          scope: operationState.scope || {},
          now: request.now,
        },
        operationState,
      );
      return {
        ok: true,
        package: request.package,
        package_version: request.package_version,
        operation: request.operation,
        output_record_ids: outputRecordIds,
        source_record_ids: sourceRecordIds,
      };
    } catch (error) {
      return {
        ok: false,
        package: request.package,
        package_version: request.package_version,
        operation: request.operation,
        output_record_ids: [],
        source_record_ids: [],
        error: {
          code: "commit_failed",
          message: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  async validateTriggerPrecondition(client, precondition, now) {
    const [kind, payload] = normalizePrecondition(precondition);
    if (!payload) return;
    const count = await this.count(client, {
      package: payload.package,
      package_version: payload.package_version,
      space: payload.space,
      scope: payload.scope,
      now,
    });
    if (kind === "ActiveCountAtLeast" && count.count < payload.threshold) {
      throw new Error(`active count ${count.count} is below threshold ${payload.threshold}`);
    }
    if (kind === "ActiveCountAtCapacity" && count.count < payload.max_records) {
      throw new Error(`active count ${count.count} is below capacity ${payload.max_records}`);
    }
  }

  async allocateOrdinal(client, request, scopeHashValue) {
    const result = await client.query(
      `
      insert into agentpm_memory_ordinals(package, package_version, space, scope_hash, next_ordinal)
      values ($1,$2,$3,$4,1)
      on conflict(package, package_version, space, scope_hash) do update set
        next_ordinal = agentpm_memory_ordinals.next_ordinal + 1
      returning next_ordinal
      `,
      [request.package, request.package_version, request.space, scopeHashValue],
    );
    return Number(result.rows[0].next_ordinal);
  }
}

function rowToRecord(row) {
  return {
    id: row.id,
    package: row.package,
    package_version: row.package_version,
    space: row.space,
    space_model: row.space_model,
    record_type: row.record_type,
    schema_version: row.schema_version,
    scope_json: row.scope_json,
    scope_hash: row.scope_hash,
    content: row.content || {},
    provenance: row.provenance || {},
    created_at: iso(row.created_at),
    updated_at: iso(row.updated_at),
    expires_at: row.expires_at ? iso(row.expires_at) : null,
    archived_at: row.archived_at ? iso(row.archived_at) : null,
    ordinal: row.ordinal === null || row.ordinal === undefined ? null : Number(row.ordinal),
  };
}

function recordParams(record) {
  return [
    record.id,
    record.package,
    record.package_version,
    record.space,
    record.space_model,
    record.record_type,
    record.schema_version,
    record.scope_json,
    record.scope_hash,
    JSON.stringify(record.content),
    JSON.stringify(record.provenance),
    record.created_at,
    record.updated_at,
    record.expires_at,
    record.archived_at,
    record.ordinal,
  ];
}

function iso(value) {
  return value instanceof Date ? value.toISOString() : new Date(value).toISOString();
}

function failedWrite(request, code, message) {
  return {
    ok: false,
    package: request.package,
    package_version: request.package_version,
    space: request.space,
    operation: request.operation,
    error: { code, message },
  };
}

function normalizePrecondition(precondition) {
  if (precondition.ActiveCountAtLeast) return ["ActiveCountAtLeast", precondition.ActiveCountAtLeast];
  if (precondition.ActiveCountAtCapacity) return ["ActiveCountAtCapacity", precondition.ActiveCountAtCapacity];
  if (precondition.active_count_at_least) return ["ActiveCountAtLeast", precondition.active_count_at_least];
  if (precondition.active_count_at_capacity) return ["ActiveCountAtCapacity", precondition.active_count_at_capacity];
  if (precondition.type === "active_count_at_least") return ["ActiveCountAtLeast", precondition];
  if (precondition.type === "active_count_at_capacity") return ["ActiveCountAtCapacity", precondition];
  return [undefined, undefined];
}

const config = providerConfig("pgvector-memory-reference");
const databaseUrl = process.env.PGVECTOR_DATABASE_URL;
if (!databaseUrl) {
  throw new Error("PGVECTOR_DATABASE_URL is required for pgvector-memory-reference");
}
const store = await PostgresMemoryStore.open(databaseUrl);

try {
  await serveMemoryRuntimeProcess(
    config.runtimeId,
    store.handle.bind(store),
    pgvectorCapabilities(config),
  );
} finally {
  await store.close();
}
