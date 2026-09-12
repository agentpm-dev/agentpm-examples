import { randomUUID } from "node:crypto";
import { createClient } from "redis";
import { serveMemoryRuntimeProcess } from "@agentpm/sdk";
import {
  contentMatchesFilterPath,
  durableContentHash,
  lifecycleWatermarkWithCommitRecords,
  providerConfig,
  redisCapabilities,
  referenceExpiresAt,
  scopeHash,
  sortMemoryRecords,
  stableScopeJson,
  unsupportedSemanticReadResult,
  unwrapRequest,
} from "./lib.mjs";

const PREFIX = "agentpm:m16:memory";

class RedisMemoryStore {
  constructor(client) {
    this.client = client;
  }

  static async open(redisUrl) {
    const client = createClient({ url: redisUrl });
    await client.connect();
    return new RedisMemoryStore(client);
  }

  async close() {
    await this.client.quit();
  }

  async handle(method, payload) {
    const request = unwrapRequest(payload);
    switch (method) {
      case "read":
        return this.read(request);
      case "write":
        return this.write(request);
      case "count":
        return this.count(request);
      case "load_operation_state":
        return this.loadOperationState(request);
      case "store_operation_state":
        return this.storeOperationState(request, payload?.state ?? request.state);
      case "commit_lifecycle":
        return this.commitLifecycle(request);
      default:
        throw new Error(`unsupported MemoryRuntime method ${method}`);
    }
  }

  async activeRecords(request) {
    const scopeJson = stableScopeJson(request.scope || {});
    const ids = request.record_id
      ? [request.record_id]
      : await this.client.sMembers(activeSetKey(request.package, request.package_version, request.space, scopeHash(scopeJson)));
    const now = new Date(request.now || Date.now());
    const records = [];
    for (const id of ids) {
      const record = await this.readRecord(id);
      if (
        record &&
        record.package === request.package &&
        record.package_version === request.package_version &&
        record.space === request.space &&
        record.scope_hash === scopeHash(scopeJson) &&
        (!request.record_type || record.record_type === request.record_type) &&
        !record.archived_at &&
        (!record.expires_at || new Date(record.expires_at) > now)
      ) {
        records.push(record);
      }
    }
    return sortMemoryRecords(records);
  }

  async read(request) {
    if (request.mode === "semantic") {
      return unsupportedSemanticReadResult(request);
    }
    let records = await this.activeRecords(request);
    if (request.mode === "filter") {
      for (const [path, expected] of Object.entries(request.filter || {})) {
        records = records.filter((record) => contentMatchesFilterPath(record.content, path, expected));
      }
    }
    if (request.mode === "full_text" && request.query) {
      const query = String(request.query).toLowerCase();
      records = records.filter((record) => JSON.stringify(record.content).toLowerCase().includes(query));
    }
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

  async write(request, multi = undefined) {
    const operation = request.operation;
    if (operation === "delete" || operation === "archive") {
      return this.mutateExisting(request, operation, multi);
    }

    const existing = await this.findExistingForWrite(request);
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
        ? await this.allocateOrdinal(request, scopeHashValue)
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
    const transaction = multi || this.client.multi();
    this.queueStoreRecord(transaction, record);
    if (!multi) {
      await transaction.exec();
    }
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

  async findExistingForWrite(request) {
    if (request.record_id) {
      return this.readRecord(request.record_id);
    }
    if (request.space_model === "document") {
      return (await this.activeRecords(request))[0];
    }
    return undefined;
  }

  async mutateExisting(request, operation, multi = undefined) {
    const records = await this.activeRecords(request);
    const transaction = multi || this.client.multi();
    const now = request.now || new Date().toISOString();
    for (const record of records) {
      const setKey = activeSetKey(record.package, record.package_version, record.space, record.scope_hash);
      if (operation === "delete") {
        transaction.del(recordKey(record.id));
        transaction.sRem(setKey, record.id);
      } else {
        const archived = { ...record, archived_at: now, updated_at: now };
        queueRecordHash(transaction, archived);
        transaction.sRem(setKey, record.id);
      }
    }
    if (!multi) await transaction.exec();
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

  async count(request) {
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      count: (await this.activeRecords(request)).length,
    };
  }

  async loadOperationState(request) {
    const raw = await this.client.get(operationStateKey(request.package, request.package_version, request.operation, request.scope || {}));
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
      state: raw ? JSON.parse(raw) : null,
    };
  }

  async storeOperationState(request, state, multi = undefined) {
    const transaction = multi || this.client.multi();
    transaction.set(operationStateKey(request.package, request.package_version, request.operation, request.scope || state?.scope || {}), JSON.stringify(state || {}));
    if (!multi) await transaction.exec();
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
    };
  }

  async commitLifecycle(request) {
    const sourceKeys = (request.expected_sources || []).map((source) => recordKey(source.record_id || source.id));
    for (let attempt = 0; attempt < 5; attempt += 1) {
      if (sourceKeys.length > 0) await this.client.watch(sourceKeys);
      try {
        if (request.trigger_precondition) {
          await this.validateTriggerPrecondition(request.trigger_precondition, request.now);
        }
        for (const source of request.expected_sources || []) {
          const recordId = source.record_id || source.id;
          const record = await this.readRecord(recordId);
          if (!record || durableContentHash(record.content) !== source.content_hash) {
            throw new Error(`stale lifecycle source ${recordId}`);
          }
        }

        const transaction = this.client.multi();
        const outputRecordIds = [];
        const sourceRecordIds = [];
        for (const write of request.output_writes || []) {
          const result = await this.write(write, transaction);
          if (!result.ok) throw new Error(result.error?.message || "output write failed");
          if (result.record_id) outputRecordIds.push(result.record_id);
        }
        for (const write of request.source_mutations || []) {
          const result = await this.write(write, transaction);
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
          {
            package: request.package,
            package_version: request.package_version,
            operation: request.operation,
            scope: operationState.scope || {},
          },
          operationState,
          transaction,
        );
        const committed = await transaction.exec();
        if (committed === null) continue;
        return {
          ok: true,
          package: request.package,
          package_version: request.package_version,
          operation: request.operation,
          output_record_ids: outputRecordIds,
          source_record_ids: sourceRecordIds,
        };
      } catch (error) {
        await this.client.unwatch().catch(() => undefined);
        if (error?.constructor?.name === "WatchError") {
          continue;
        }
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
    return {
      ok: false,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
      output_record_ids: [],
      source_record_ids: [],
      error: {
        code: "commit_failed",
        message: "Redis MemoryRuntime state changed too frequently to commit atomically",
      },
    };
  }

  async validateTriggerPrecondition(precondition, now) {
    const [kind, payload] = normalizePrecondition(precondition);
    if (!payload) return;
    const count = await this.count({
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

  async readRecord(id) {
    const hash = await this.client.hGetAll(recordKey(id));
    return hash && hash.id ? recordFromHash(hash) : undefined;
  }

  queueStoreRecord(transaction, record) {
    queueRecordHash(transaction, record);
    transaction.sAdd(activeSetKey(record.package, record.package_version, record.space, record.scope_hash), record.id);
  }

  async allocateOrdinal(request, scopeHashValue) {
    return this.client.incr(ordinalKey(request.package, request.package_version, request.space, scopeHashValue));
  }
}

function queueRecordHash(transaction, record) {
  transaction.hSet(recordKey(record.id), {
    id: record.id,
    package: record.package,
    package_version: record.package_version,
    space: record.space,
    space_model: record.space_model,
    record_type: record.record_type,
    schema_version: record.schema_version,
    scope_json: record.scope_json,
    scope_hash: record.scope_hash,
    content: JSON.stringify(record.content),
    provenance: JSON.stringify(record.provenance),
    created_at: record.created_at,
    updated_at: record.updated_at,
    expires_at: record.expires_at || "",
    archived_at: record.archived_at || "",
    ordinal: record.ordinal === null || record.ordinal === undefined ? "" : String(record.ordinal),
  });
}

function recordFromHash(hash) {
  return {
    id: hash.id,
    package: hash.package,
    package_version: hash.package_version,
    space: hash.space,
    space_model: hash.space_model,
    record_type: hash.record_type,
    schema_version: hash.schema_version,
    scope_json: hash.scope_json,
    scope_hash: hash.scope_hash,
    content: hash.content ? JSON.parse(hash.content) : {},
    provenance: hash.provenance ? JSON.parse(hash.provenance) : {},
    created_at: hash.created_at,
    updated_at: hash.updated_at,
    expires_at: hash.expires_at || null,
    archived_at: hash.archived_at || null,
    ordinal: hash.ordinal ? Number(hash.ordinal) : null,
  };
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

function activeSetKey(packageName, version, space, scopeHashValue) {
  return `${PREFIX}:active:${encode(packageName)}:${encode(version)}:${encode(space)}:${encode(scopeHashValue)}`;
}

function recordKey(id) {
  return `${PREFIX}:record:${encode(id)}`;
}

function operationStateKey(packageName, version, operation, scope) {
  const scopeJson = stableScopeJson(scope || {});
  return `${PREFIX}:operation-state:${encode(packageName)}:${encode(version)}:${encode(operation)}:${encode(scopeHash(scopeJson))}`;
}

function ordinalKey(packageName, version, space, scopeHashValue) {
  return `${PREFIX}:ordinal:${encode(packageName)}:${encode(version)}:${encode(space)}:${encode(scopeHashValue)}`;
}

function encode(value) {
  return Buffer.from(String(value)).toString("base64url");
}

const config = providerConfig("redis-memory-reference");
const redisUrl = process.env.REDIS_URL;
if (!redisUrl) {
  throw new Error("REDIS_URL is required for redis-memory-reference");
}
const store = await RedisMemoryStore.open(redisUrl);

try {
  await serveMemoryRuntimeProcess(
    config.runtimeId,
    store.handle.bind(store),
    redisCapabilities(config),
  );
} finally {
  await store.close();
}
