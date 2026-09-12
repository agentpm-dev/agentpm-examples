import { createHash, randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";

export function providerConfig(defaultRuntimeId) {
  const pgvectorSemantic = process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC === "true";
  const redisSemantic = process.env.AGENTPM_MEMORY_REDIS_STACK === "true";
  if (pgvectorSemantic) {
    throw new Error(
      "AGENTPM_MEMORY_PGVECTOR_SEMANTIC=true is not supported yet; semantic retrieval requires real pgvector embedding storage and ranking.",
    );
  }
  if (redisSemantic) {
    throw new Error(
      "AGENTPM_MEMORY_REDIS_STACK=true is not supported yet; semantic retrieval requires real Redis Stack vector storage and ranking.",
    );
  }
  return {
    runtimeId: process.env.AGENTPM_MEMORY_RUNTIME_ID || defaultRuntimeId,
    packageName: process.env.AGENTPM_MEMORY_PACKAGE || "@zack/m16-reference-memory",
    version: process.env.AGENTPM_MEMORY_VERSION || "0.1.0",
    pgvectorSemantic,
    redisSemantic,
  };
}

export function pgvectorCapabilities(config) {
  if (config.pgvectorSemantic) {
    throw new Error("semantic retrieval is not implemented by the M16 pgvector reference provider");
  }
  return {
    descriptor: {
      space_models: ["document", "collection", "sequence"],
      retrieval_modes: ["key", "filter", "chronological", "full_text"],
      retention_actions: ["delete", "archive"],
      constraints: ["append_only"],
      capacity: true,
      durable_trigger_state: true,
      atomic_batches: true,
    },
    packages: [{ package: config.packageName, version: config.version, ready: true }],
  };
}

export function redisCapabilities(config) {
  if (config.redisSemantic) {
    throw new Error("semantic retrieval is not implemented by the M16 Redis reference provider");
  }
  return {
    descriptor: {
      space_models: ["document", "collection", "sequence"],
      retrieval_modes: ["key", "filter", "chronological", "full_text"],
      retention_actions: ["delete", "archive"],
      constraints: ["append_only"],
      capacity: true,
      durable_trigger_state: true,
      atomic_batches: false,
    },
    packages: [{ package: config.packageName, version: config.version, ready: true }],
  };
}

export function stableScopeJson(scope) {
  return JSON.stringify(
    Object.fromEntries(Object.entries(scope || {}).sort(([left], [right]) => left.localeCompare(right))),
  );
}

export function scopeHash(scopeJson) {
  return `sha256:${createHash("sha256").update(scopeJson).digest("hex")}`;
}

export function durableContentHash(content) {
  return `sha256:${createHash("sha256").update(JSON.stringify(content ?? {})).digest("hex")}`;
}

export function unwrapRequest(payload) {
  if (!payload || typeof payload !== "object") return {};
  return payload.request && typeof payload.request === "object" ? payload.request : payload;
}

export function contentMatchesFilterPath(value, path, expected) {
  const segments = Array.isArray(path) ? path : String(path).split(".");
  if (segments.length === 0 && isDeepStrictEqual(value, expected)) return true;
  if (Array.isArray(value)) return value.some((entry) => contentMatchesFilterPath(entry, segments, expected));
  if (value && typeof value === "object" && segments.length > 0) {
    const [head, ...tail] = segments;
    return Object.hasOwn(value, head) && contentMatchesFilterPath(value[head], tail, expected);
  }
  return false;
}

export function isActive(record, now = new Date()) {
  return !record.archived_at && (!record.expires_at || new Date(record.expires_at) > now);
}

export function referenceExpiresAt(space, now) {
  const retentionDays = {
    current_note: 30,
    notes: 30,
    summaries: 90,
  }[space];
  if (!retentionDays) return null;
  return new Date(new Date(now).getTime() + retentionDays * 24 * 60 * 60 * 1000).toISOString();
}

export function sortMemoryRecords(records) {
  return [...records].sort((left, right) => {
    const leftOrdinal = left.ordinal ?? Number.MAX_SAFE_INTEGER;
    const rightOrdinal = right.ordinal ?? Number.MAX_SAFE_INTEGER;
    if (leftOrdinal !== rightOrdinal) return leftOrdinal - rightOrdinal;
    return left.created_at.localeCompare(right.created_at) || left.id.localeCompare(right.id);
  });
}

export function unsupportedSemanticReadResult(request) {
  return {
    ok: false,
    package: request.package,
    package_version: request.package_version,
    space: request.space,
    mode: request.mode,
    records: [],
    count: 0,
    embedding_requests: 0,
    vectors_materialized: 0,
    vectors_pending: 0,
    error: {
      code: "unsupported_capability",
      message: "semantic retrieval is not implemented by the M16 reference providers",
    },
  };
}

export function lifecycleWatermarkWithCommitRecords(watermark, outputRecordIds, sourceRecordIds) {
  return {
    ...(watermark && typeof watermark === "object" && !Array.isArray(watermark) ? watermark : {}),
    last_output_record_ids: outputRecordIds,
    last_mutated_source_record_ids: sourceRecordIds,
  };
}

export class ReferenceMemoryStore {
  constructor() {
    this.records = new Map();
    this.operationStates = new Map();
    this.nextOrdinal = new Map();
  }

  snapshot() {
    return {
      records: [...this.records.entries()],
      operationStates: [...this.operationStates.entries()],
      nextOrdinal: [...this.nextOrdinal.entries()],
    };
  }

  restore(snapshot) {
    this.records = new Map(snapshot?.records || []);
    this.operationStates = new Map(snapshot?.operationStates || []);
    this.nextOrdinal = new Map(snapshot?.nextOrdinal || []);
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

  activeRecords(request) {
    const requestScope = stableScopeJson(request.scope || {});
    const now = new Date(request.now || Date.now());
    return [...this.records.values()].filter(
      (record) =>
        record.package === request.package &&
        record.package_version === request.package_version &&
        record.space === request.space &&
        record.scope_json === requestScope &&
        (!request.record_type || record.record_type === request.record_type) &&
        isActive(record, now),
    );
  }

  read(request) {
    if (request.mode === "semantic") {
      return unsupportedSemanticReadResult(request);
    }
    let records = this.activeRecords(request);
    if (request.mode === "key" && request.record_id) {
      records = records.filter((record) => record.id === request.record_id);
    }
    if (request.mode === "filter") {
      for (const [path, expected] of Object.entries(request.filter || {})) {
        records = records.filter((record) => contentMatchesFilterPath(record.content, path, expected));
      }
    }
    if (request.mode === "full_text") {
      const query = String(request.query || "").toLowerCase();
      records = query
        ? records.filter((record) => JSON.stringify(record.content).toLowerCase().includes(query))
        : records;
    }
    records = records.sort((left, right) => {
      const leftOrdinal = left.ordinal ?? Number.MAX_SAFE_INTEGER;
      const rightOrdinal = right.ordinal ?? Number.MAX_SAFE_INTEGER;
      if (leftOrdinal !== rightOrdinal) return leftOrdinal - rightOrdinal;
      return left.created_at.localeCompare(right.created_at) || left.id.localeCompare(right.id);
    });
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

  write(request) {
    const operation = request.operation;
    if (operation === "delete" || operation === "archive") {
      return this.mutateExisting(request, operation);
    }
    const existing =
      request.record_id && this.records.has(request.record_id)
        ? this.records.get(request.record_id)
        : request.space_model === "document"
          ? this.activeRecords(request)[0]
          : undefined;
    if (operation === "update" && !existing) {
      return this.failedWrite(request, "not_found", "record not found");
    }
    if (operation === "create" && request.space_model === "document" && existing) {
      return this.failedWrite(request, "conflict", "document already exists");
    }
    const now = request.now || new Date().toISOString();
    const id = existing?.id || request.record_id || `mem-${randomUUID()}`;
    const scopeJson = stableScopeJson(request.scope || {});
    const ordinal =
      request.space_model === "sequence" && !existing ? this.allocateOrdinal(request, scopeJson) : existing?.ordinal ?? null;
    const record = {
      id,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      space_model: request.space_model,
      record_type: request.record_type,
      schema_version: request.schema_version,
      scope_json: scopeJson,
      scope_hash: scopeHash(scopeJson),
      content: request.content ?? {},
      provenance: request.provenance ?? {},
      created_at: existing?.created_at || now,
      updated_at: now,
      expires_at: existing?.expires_at || null,
      archived_at: null,
      ordinal,
    };
    this.records.set(id, record);
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

  mutateExisting(request, operation) {
    const records = request.record_id
      ? [...this.records.values()].filter((record) => record.id === request.record_id)
      : this.activeRecords(request);
    const now = request.now || new Date().toISOString();
    for (const record of records) {
      if (operation === "delete") {
        this.records.delete(record.id);
      } else {
        this.records.set(record.id, { ...record, archived_at: now, updated_at: now });
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

  count(request) {
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      count: this.activeRecords(request).length,
    };
  }

  loadOperationState(request) {
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
      state: this.operationStates.get(this.stateKey(request)) || null,
    };
  }

  storeOperationState(request, state) {
    this.operationStates.set(this.stateKey(request), state);
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
    };
  }

  commitLifecycle(request) {
    const records = new Map(this.records);
    const states = new Map(this.operationStates);
    try {
      for (const source of request.expected_sources || []) {
        const record = this.records.get(source.id);
        if (!record || durableContentHash(record.content) !== source.content_hash) {
          throw new Error(`stale lifecycle source ${source.id}`);
        }
      }
      const outputIds = [];
      const sourceIds = [];
      for (const write of request.output_writes || []) {
        const result = this.write(write);
        if (!result.ok) throw new Error(result.error?.message || "output write failed");
        outputIds.push(result.record_id);
      }
      for (const write of request.source_mutations || []) {
        const result = this.write(write);
        if (!result.ok) throw new Error(result.error?.message || "source mutation failed");
        if (result.record_id) sourceIds.push(result.record_id);
      }
      this.operationStates.set(
        this.stateKey({
          package: request.package,
          package_version: request.package_version,
          operation: request.operation,
          scope: request.operation_state?.scope || {},
        }),
        request.operation_state,
      );
      return {
        ok: true,
        package: request.package,
        package_version: request.package_version,
        operation: request.operation,
        output_record_ids: outputIds.filter(Boolean),
        source_record_ids: sourceIds,
      };
    } catch (error) {
      this.records = records;
      this.operationStates = states;
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

  allocateOrdinal(request, scopeJson) {
    const key = `${request.package}\0${request.package_version}\0${request.space}\0${scopeJson}`;
    const ordinal = (this.nextOrdinal.get(key) || 0) + 1;
    this.nextOrdinal.set(key, ordinal);
    return ordinal;
  }

  stateKey(request) {
    return `${request.package}\0${request.package_version}\0${request.operation}\0${stableScopeJson(request.scope || {})}`;
  }

  failedWrite(request, code, message) {
    return {
      ok: false,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      operation: request.operation,
      error: { code, message },
    };
  }
}
