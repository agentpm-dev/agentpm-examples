import test from "node:test";
import assert from "node:assert/strict";

import {
  ReferenceMemoryStore,
  durableContentHash,
  pgvectorCapabilities,
  providerConfig,
  redisCapabilities,
} from "../providers/node/lib.mjs";
import {
  runMemoryRuntimeConformance,
  sqliteCapabilities,
} from "./support/conformance.mjs";

const baseRequest = {
  package: "@zack/m16-reference-memory",
  package_version: "0.1.0",
  space: "notes",
  space_model: "collection",
  record_type: "note",
  schema_version: "1.0.0",
  scope: { user: "m16-user" },
  provenance: { harness: { kind: "test" } },
  now: "2026-09-11T00:00:00Z",
};

test("pgvector capabilities omit semantic and reject the unfinished semantic flag", () => {
  assert.deepEqual(
    pgvectorCapabilities({
      packageName: "@zack/m16-reference-memory",
      version: "0.1.0",
      pgvectorSemantic: false,
    }),
    {
      descriptor: {
        space_models: ["document", "collection", "sequence"],
        retrieval_modes: ["key", "filter", "chronological", "full_text"],
        retention_actions: ["delete", "archive"],
        constraints: ["append_only"],
        capacity: true,
        durable_trigger_state: true,
        atomic_batches: true,
      },
      packages: [
        {
          package: "@zack/m16-reference-memory",
          version: "0.1.0",
          ready: true,
        },
      ],
    },
  );
  assert.throws(
    () => pgvectorCapabilities({
      packageName: "pkg",
      version: "0.1.0",
      pgvectorSemantic: true,
    }),
    /semantic retrieval is not implemented/,
  );
});

test("redis capabilities omit semantic and reject the unfinished Redis Stack flag", () => {
  const capabilities = redisCapabilities({
    packageName: "@zack/m16-reference-memory",
    version: "0.1.0",
    redisSemantic: false,
  });
  assert.deepEqual(
    capabilities.descriptor.retrieval_modes,
    ["key", "filter", "chronological", "full_text"],
  );
  assert.equal(capabilities.descriptor.durable_trigger_state, true);
  assert.equal(capabilities.descriptor.atomic_batches, false);
  assert.throws(
    () => redisCapabilities({ packageName: "pkg", version: "0.1.0", redisSemantic: true }),
    /semantic retrieval is not implemented/,
  );
});

test("provider config defaults to the M16 reference package", () => {
  assert.equal(providerConfig("pgvector-memory-reference").packageName, "@zack/m16-reference-memory");
});

test("provider config rejects semantic env flags until vector retrieval is implemented", () => {
  const previousPgvector = process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC;
  const previousRedis = process.env.AGENTPM_MEMORY_REDIS_STACK;
  try {
    process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC = "true";
    assert.throws(() => providerConfig("pgvector-memory-reference"), /AGENTPM_MEMORY_PGVECTOR_SEMANTIC=true is not supported yet/);
    delete process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC;
    process.env.AGENTPM_MEMORY_REDIS_STACK = "true";
    assert.throws(() => providerConfig("redis-memory-reference"), /AGENTPM_MEMORY_REDIS_STACK=true is not supported yet/);
  } finally {
    if (previousPgvector === undefined) delete process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC;
    else process.env.AGENTPM_MEMORY_PGVECTOR_SEMANTIC = previousPgvector;
    if (previousRedis === undefined) delete process.env.AGENTPM_MEMORY_REDIS_STACK;
    else process.env.AGENTPM_MEMORY_REDIS_STACK = previousRedis;
  }
});

test("store handles direct write, filter read, count, and operation state", async () => {
  const store = new ReferenceMemoryStore();
  const write = await store.handle("write", {
    request: {
      ...baseRequest,
      operation: "create",
      content: { body: "alpha note", topic: "launch" },
    },
  });
  assert.equal(write.ok, true);
  assert.match(write.record_id, /^mem-/);

  const read = await store.handle("read", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      space: baseRequest.space,
      scope: baseRequest.scope,
      mode: "filter",
      record_type: "note",
      filter: { topic: "launch" },
      now: baseRequest.now,
    },
  });
  assert.equal(read.count, 1);
  assert.equal(read.records[0].content.body, "alpha note");

  const semanticRead = await store.handle("read", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      space: baseRequest.space,
      scope: baseRequest.scope,
      mode: "semantic",
      record_type: "note",
      query: "launch",
      now: baseRequest.now,
    },
  });
  assert.equal(semanticRead.ok, false);
  assert.equal(semanticRead.error.code, "unsupported_capability");
  assert.equal(semanticRead.embedding_requests, 0);

  const count = await store.handle("count", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      space: baseRequest.space,
      scope: baseRequest.scope,
      record_type: "note",
      now: baseRequest.now,
    },
  });
  assert.equal(count.count, 1);

  await store.handle("store_operation_state", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      operation: "summarize_notes",
      scope: baseRequest.scope,
      now: baseRequest.now,
    },
    state: { armed: true, trigger_type: "record_count" },
  });
  const state = await store.handle("load_operation_state", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      operation: "summarize_notes",
      scope: baseRequest.scope,
      now: baseRequest.now,
    },
  });
  assert.deepEqual(state.state, { armed: true, trigger_type: "record_count" });
});

test("lifecycle commit writes outputs, mutates sources, and rolls back stale commits", async () => {
  const store = new ReferenceMemoryStore();
  const source = await store.handle("write", {
    request: {
      ...baseRequest,
      operation: "create",
      content: { body: "source note", topic: "ops" },
    },
  });
  const outputWrite = {
    ...baseRequest,
    space: "summaries",
    record_type: "summary",
    operation: "create",
    content: { summary: "source note", source_count: 1 },
  };
  const deleteSource = {
    ...baseRequest,
    operation: "delete",
    record_id: source.record_id,
    content: undefined,
  };
  const commit = await store.handle("commit_lifecycle", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      operation: "summarize_notes",
      expected_sources: [
        {
          id: source.record_id,
          content_hash: durableContentHash(source.record.content),
        },
      ],
      output_writes: [outputWrite],
      source_mutations: [deleteSource],
      operation_state: {
        package: baseRequest.package,
        package_version: baseRequest.package_version,
        operation: "summarize_notes",
        scope: baseRequest.scope,
        trigger_type: "record_count",
        armed: true,
        updated_at: baseRequest.now,
      },
      now: baseRequest.now,
    },
  });
  assert.equal(commit.ok, true);
  assert.equal(commit.output_record_ids.length, 1);
  assert.deepEqual(commit.source_record_ids, [source.record_id]);

  const stale = await store.handle("commit_lifecycle", {
    request: {
      package: baseRequest.package,
      package_version: baseRequest.package_version,
      operation: "summarize_notes",
      expected_sources: [{ id: source.record_id, content_hash: "sha256:stale" }],
      output_writes: [outputWrite],
      source_mutations: [],
      operation_state: { scope: baseRequest.scope },
      now: baseRequest.now,
    },
  });
  assert.equal(stale.ok, false);
  assert.equal(stale.error.code, "commit_failed");
});

test("cross-backend conformance uses one scenario with advertised capability skips", async () => {
  const fixtures = [
    {
      name: "sqlite",
      capabilities: sqliteCapabilities(),
      store: new ReferenceMemoryStore(),
      expectedSkips: [],
    },
    {
      name: "pgvector",
      capabilities: pgvectorCapabilities({
        packageName: "@zack/m16-reference-memory",
        version: "0.1.0",
        pgvectorSemantic: false,
      }),
      store: new ReferenceMemoryStore(),
      expectedSkips: [],
    },
    {
      name: "redis",
      capabilities: redisCapabilities({
        packageName: "@zack/m16-reference-memory",
        version: "0.1.0",
        redisSemantic: false,
      }),
      store: new ReferenceMemoryStore(),
      expectedSkips: ["lifecycle_commit"],
    },
  ];

  for (const fixture of fixtures) {
    const result = await runMemoryRuntimeConformance(
      fixture.name,
      fixture.capabilities,
      (method, payload) => fixture.store.handle(method, payload),
    );
    assert.deepEqual(result.skipped, fixture.expectedSkips);
  }
});
