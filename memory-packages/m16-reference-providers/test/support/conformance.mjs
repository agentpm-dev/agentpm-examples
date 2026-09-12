import assert from "node:assert/strict";
import { durableContentHash } from "../../providers/node/lib.mjs";

export function sqliteCapabilities(packageName = "@zack/m16-reference-memory", version = "0.1.0") {
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
    packages: [{ package: packageName, version, ready: true }],
  };
}

export async function runMemoryRuntimeConformance(name, capabilities, request) {
  const descriptor = capabilities.descriptor;
  assert(descriptor, `${name} capabilities must include descriptor`);

  const packageName = capabilities.packages?.[0]?.package || "@zack/m16-reference-memory";
  const packageVersion = capabilities.packages?.[0]?.version || "0.1.0";
  const scope = { user: `m16-conformance-${name}-${Date.now()}` };
  const nowA = "2026-09-11T00:00:00Z";
  const nowB = "2026-09-11T00:00:01Z";
  const base = {
    package: packageName,
    package_version: packageVersion,
    space: "notes",
    space_model: "collection",
    record_type: "note",
    schema_version: "1.0.0",
    scope,
    provenance: { harness: { kind: "conformance-test", backend: name } },
    now: nowA,
  };

  const alpha = ok(
    await request("write", {
      request: {
        ...base,
        operation: "create",
        content: { body: "launch readiness note", topic: "launch", marker: `${name}-alpha` },
      },
    }),
  );
  const beta = ok(
    await request("write", {
      request: {
        ...base,
        now: nowB,
        operation: "create",
        content: { body: "ops handoff note", topic: "ops", marker: `${name}-beta` },
      },
    }),
  );
  assert.match(alpha.record_id, /^mem-/);
  assert.match(beta.record_id, /^mem-/);

  const keyRead = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        mode: "key",
        record_id: alpha.record_id,
        record_type: "note",
        now: nowB,
      },
    }),
  );
  assert.equal(keyRead.count, 1);
  assert.equal(keyRead.records[0].content.marker, `${name}-alpha`);

  const filterRead = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        mode: "filter",
        record_type: "note",
        filter: { topic: "ops" },
        now: nowB,
      },
    }),
  );
  assert.equal(filterRead.count, 1);
  assert.equal(filterRead.records[0].content.marker, `${name}-beta`);

  const chronologicalRead = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        mode: "chronological",
        record_type: "note",
        limit: 10,
        now: nowB,
      },
    }),
  );
  assert.deepEqual(
    chronologicalRead.records.map((record) => record.content.marker),
    [`${name}-alpha`, `${name}-beta`],
  );

  const fullTextRead = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        mode: "full_text",
        record_type: "note",
        query: "handoff",
        now: nowB,
      },
    }),
  );
  assert.equal(fullTextRead.count, 1);
  assert.equal(fullTextRead.records[0].content.marker, `${name}-beta`);

  await assertFilterConformance(name, packageName, packageVersion, request);

  const count = ok(
    await request("count", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        record_type: "note",
        now: nowB,
      },
    }),
  );
  assert.equal(count.count, 2);

  const state = {
    package: packageName,
    package_version: packageVersion,
    operation: "summarize_notes",
    scope,
    trigger_type: "record_count",
    armed: true,
    updated_at: nowB,
  };
  ok(
    await request("store_operation_state", {
      request: {
        package: packageName,
        package_version: packageVersion,
        operation: "summarize_notes",
        scope,
        now: nowB,
      },
      state,
    }),
  );
  const loadedState = ok(
    await request("load_operation_state", {
      request: {
        package: packageName,
        package_version: packageVersion,
        operation: "summarize_notes",
        scope,
        now: nowB,
      },
    }),
  );
  assert.deepEqual(loadedState.state, state);

  if (descriptor.retrieval_modes.includes("semantic")) {
    const semanticRead = ok(
      await request("read", {
        request: {
          package: packageName,
          package_version: packageVersion,
          space: "notes",
          scope,
          mode: "semantic",
          record_type: "note",
          query: "deployment readiness",
          now: nowB,
        },
      }),
    );
    assert.equal(semanticRead.count, 1);
    assert.equal(semanticRead.records[0].content.marker, `${name}-alpha`);
    assert.ok(semanticRead.embedding_requests > 0);
  }

  if (!descriptor.atomic_batches) {
    return { skipped: ["lifecycle_commit"] };
  }

  const commit = ok(
    await request("commit_lifecycle", {
      request: {
        package: packageName,
        package_version: packageVersion,
        operation: "summarize_notes",
        expected_sources: [
          {
            package: packageName,
            package_version: packageVersion,
            space: "notes",
            scope,
            record_id: alpha.record_id,
            id: alpha.record_id,
            content_hash: durableContentHash(alpha.record.content),
          },
        ],
        output_writes: [
          {
            ...base,
            space: "summaries",
            record_type: "summary",
            operation: "create",
            content: { summary: "launch readiness note", source_count: 1, marker: `${name}-summary` },
          },
        ],
        source_mutations: [
          {
            ...base,
            operation: "delete",
            record_id: alpha.record_id,
          },
        ],
        operation_state: state,
        now: nowB,
      },
    }),
  );
  assert.equal(commit.output_record_ids.length, 1);
  assert.deepEqual(commit.source_record_ids, [alpha.record_id]);

  const notesAfterCommit = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "notes",
        scope,
        mode: "chronological",
        record_type: "note",
        limit: 10,
        now: nowB,
      },
    }),
  );
  assert.deepEqual(notesAfterCommit.records.map((record) => record.content.marker), [`${name}-beta`]);

  const summariesAfterCommit = ok(
    await request("read", {
      request: {
        package: packageName,
        package_version: packageVersion,
        space: "summaries",
        scope,
        mode: "filter",
        record_type: "summary",
        filter: { marker: `${name}-summary` },
        now: nowB,
      },
    }),
  );
  assert.equal(summariesAfterCommit.count, 1);
  return { skipped: [] };
}

export function ok(result) {
  assert.equal(result?.ok, true, JSON.stringify(result));
  return result;
}

async function assertFilterConformance(name, packageName, packageVersion, request) {
  const scope = { user: `m16-filter-${name}-${Date.now()}` };
  const now = "2026-09-11T00:01:00Z";
  const base = {
    package: packageName,
    package_version: packageVersion,
    space: "notes",
    space_model: "collection",
    record_type: "note",
    schema_version: "1.0.0",
    scope,
    provenance: { harness: { kind: "filter-conformance-test", backend: name } },
    now,
  };
  const matchMarker = `${name}-filter-match`;
  const otherMarker = `${name}-filter-other`;
  ok(
    await request("write", {
      request: {
        ...base,
        operation: "create",
        content: {
          marker: matchMarker,
          topic: "launch",
          status: "ready",
          tags: ["alpha", "beta"],
          nested: { level: { value: "deep" } },
          members: [{ name: "no" }, { name: "target" }],
          groups: [{ items: [{ name: "x" }] }],
          arrayValue: [{ code: "a" }, { code: "b" }],
          a: { b: 1 },
          presentNull: null,
        },
      },
    }),
  );
  ok(
    await request("write", {
      request: {
        ...base,
        operation: "create",
        content: {
          marker: otherMarker,
          topic: "other",
          status: "draft",
          tags: ["gamma"],
          nested: { level: { value: "shallow" } },
          members: [{ name: "other" }],
          groups: [{ items: [{ name: "y" }] }],
          arrayValue: [{ code: "z" }],
          a: { b: 1 },
        },
      },
    }),
  );

  await assertFilterMarkers("top-level scalar equality", { topic: "launch" }, [matchMarker]);
  await assertFilterMarkers("leaf-array containment", { tags: "beta" }, [matchMarker]);
  await assertFilterMarkers("nested object path", { "nested.level.value": "deep" }, [matchMarker]);
  await assertFilterMarkers("array of objects mid-path", { "members.name": "target" }, [matchMarker]);
  await assertFilterMarkers("nested arrays mid-path", { "groups.items.name": "x" }, [matchMarker]);
  await assertFilterMarkers("present null value", { presentNull: null }, [matchMarker]);
  await assertFilterMarkers("absent path with null value", { "a.c": null }, []);
  await assertFilterMarkers("whole-array structural equality", { arrayValue: [{ code: "a" }, { code: "b" }] }, [
    matchMarker,
  ]);
  await assertFilterMarkers("conjunctive multi-key", { topic: "launch", status: "ready" }, [matchMarker]);
  await assertFilterMarkers("non-matching value", { topic: "missing" }, []);

  async function assertFilterMarkers(label, filter, expectedMarkers) {
    const read = ok(
      await request("read", {
        request: {
          package: packageName,
          package_version: packageVersion,
          space: "notes",
          scope,
          mode: "filter",
          record_type: "note",
          filter,
          now,
        },
      }),
    );
    assert.deepEqual(
      read.records.map((record) => record.content.marker).sort(),
      expectedMarkers.sort(),
      label,
    );
  }
}
