import { createHash, randomUUID } from 'node:crypto';
import { serve } from './service-io.mjs';

const RUNTIME_ID = 'reference-memory';
const PACKAGE = '@zack/support-customer-state';
const VERSION = '0.1.0';

const records = new Map();
const operationStates = new Map();
const nextOrdinal = new Map();

await serve('memory', {
  initialize() {
    return {
      registry_id: process.env.PROVIDER_LAB_MEMORY_RUNTIME_ID || RUNTIME_ID,
      ready: true,
      capabilities: {
        descriptor: {
          space_models: ['document', 'collection', 'sequence'],
          retrieval_modes: ['key', 'filter', 'chronological', 'full_text'],
          retention_actions: ['delete', 'archive'],
          constraints: ['append_only'],
          capacity: true,
          durable_trigger_state: true,
          atomic_batches: false,
        },
        packages: [{ package: PACKAGE, version: VERSION, ready: true }],
      },
    };
  },
  read(payload) {
    return read(unwrapRequest(payload));
  },
  write(payload) {
    return write(unwrapRequest(payload));
  },
  count(payload) {
    const request = unwrapRequest(payload);
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      space: request.space,
      count: activeRecords(request).length,
    };
  },
  load_operation_state(payload) {
    const request = unwrapRequest(payload);
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
      state: operationStates.get(stateKey(request)) || null,
    };
  },
  store_operation_state(payload) {
    const request = unwrapRequest(payload);
    operationStates.set(stateKey(request), payload.state ?? request.state ?? {});
    return {
      ok: true,
      package: request.package,
      package_version: request.package_version,
      operation: request.operation,
    };
  },
  commit_lifecycle(payload) {
    return {
      ok: true,
      package: payload.package,
      package_version: payload.package_version,
      operation: payload.operation,
      output_record_ids: [],
      source_record_ids: [],
    };
  },
});

function read(request) {
  validatePackage(request);
  if (request.mode === 'semantic') {
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
        code: 'unsupported_capability',
        message: 'The compact provider lab MemoryRuntime does not implement semantic reads.',
      },
    };
  }

  let matches = activeRecords(request);
  if (request.mode === 'key' && request.record_id) {
    matches = matches.filter((record) => record.id === request.record_id);
  }
  if (request.mode === 'filter') {
    for (const [path, expected] of Object.entries(request.filter || {})) {
      matches = matches.filter((record) => contentMatchesFilterPath(record.content, path, expected));
    }
  }
  if (request.mode === 'full_text' && request.query) {
    const query = String(request.query).toLowerCase();
    matches = matches.filter((record) => JSON.stringify(record.content).toLowerCase().includes(query));
  }
  if (request.limit) matches = matches.slice(0, request.limit);

  return {
    ok: true,
    package: request.package,
    package_version: request.package_version,
    space: request.space,
    mode: request.mode,
    records: matches,
    count: matches.length,
    embedding_requests: 0,
    vectors_materialized: 0,
    vectors_pending: 0,
  };
}

function write(request) {
  validatePackage(request);
  if (request.operation === 'delete' || request.operation === 'archive') {
    return mutateExisting(request);
  }

  const existing =
    request.record_id && records.has(request.record_id)
      ? records.get(request.record_id)
      : request.space_model === 'document'
        ? activeRecords(request)[0]
        : undefined;
  if (request.operation === 'update' && !existing) {
    return failedWrite(request, 'not_found', 'record not found');
  }
  if (request.operation === 'create' && request.space_model === 'document' && existing) {
    return failedWrite(request, 'conflict', 'document already exists');
  }

  const now = request.now || new Date().toISOString();
  const scopeJson = stableScopeJson(request.scope || {});
  const id = existing?.id || request.record_id || `mem-${randomUUID()}`;
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
    ordinal:
      request.space_model === 'sequence' && !existing
        ? allocateOrdinal(request, scopeJson)
        : existing?.ordinal ?? null,
  };
  records.set(id, record);

  return {
    ok: true,
    package: request.package,
    package_version: request.package_version,
    space: request.space,
    operation: request.operation,
    record_id: id,
    record,
    embedding_requests: 0,
  };
}

function mutateExisting(request) {
  const matches = request.record_id
    ? [...records.values()].filter((record) => record.id === request.record_id)
    : activeRecords(request);
  const now = request.now || new Date().toISOString();
  for (const record of matches) {
    if (request.operation === 'delete') {
      records.delete(record.id);
    } else {
      records.set(record.id, { ...record, archived_at: now, updated_at: now });
    }
  }
  return {
    ok: true,
    package: request.package,
    package_version: request.package_version,
    space: request.space,
    operation: request.operation,
    record_id: matches[0]?.id,
    record: matches[0],
    embedding_requests: 0,
  };
}

function activeRecords(request) {
  const requestScope = stableScopeJson(request.scope || {});
  const now = new Date(request.now || Date.now());
  return [...records.values()]
    .filter(
      (record) =>
        record.package === request.package &&
        record.package_version === request.package_version &&
        record.space === request.space &&
        record.scope_json === requestScope &&
        (!request.record_type || record.record_type === request.record_type) &&
        !record.archived_at &&
        (!record.expires_at || new Date(record.expires_at) > now),
    )
    .sort((left, right) => {
      const leftOrdinal = left.ordinal ?? Number.MAX_SAFE_INTEGER;
      const rightOrdinal = right.ordinal ?? Number.MAX_SAFE_INTEGER;
      if (leftOrdinal !== rightOrdinal) return leftOrdinal - rightOrdinal;
      return left.created_at.localeCompare(right.created_at) || left.id.localeCompare(right.id);
    });
}

function validatePackage(request) {
  if (request.package !== PACKAGE) {
    throw new Error(`request package ${request.package} does not match ${PACKAGE}`);
  }
  if (request.package_version !== VERSION) {
    throw new Error(`request version ${request.package_version} does not match ${VERSION}`);
  }
}

function unwrapRequest(payload) {
  if (!payload || typeof payload !== 'object') return {};
  return payload.request && typeof payload.request === 'object' ? payload.request : payload;
}

function stableScopeJson(scope) {
  return JSON.stringify(
    Object.fromEntries(Object.entries(scope || {}).sort(([left], [right]) => left.localeCompare(right))),
  );
}

function scopeHash(scopeJson) {
  return `sha256:${createHash('sha256').update(scopeJson).digest('hex')}`;
}

function contentMatchesFilterPath(value, path, expected) {
  const segments = Array.isArray(path) ? path : String(path).split('.');
  if (segments.length === 0 && JSON.stringify(value) === JSON.stringify(expected)) return true;
  if (Array.isArray(value)) return value.some((entry) => contentMatchesFilterPath(entry, segments, expected));
  if (value && typeof value === 'object' && segments.length > 0) {
    const [head, ...tail] = segments;
    return Object.hasOwn(value, head) && contentMatchesFilterPath(value[head], tail, expected);
  }
  return false;
}

function allocateOrdinal(request, scopeJson) {
  const key = `${request.package}\0${request.package_version}\0${request.space}\0${scopeJson}`;
  const next = (nextOrdinal.get(key) || 0) + 1;
  nextOrdinal.set(key, next);
  return next;
}

function stateKey(request) {
  return `${request.package}\0${request.package_version}\0${request.operation}\0${stableScopeJson(request.scope || {})}`;
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
