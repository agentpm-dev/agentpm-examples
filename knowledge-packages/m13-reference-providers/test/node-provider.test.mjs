import test from "node:test";
import assert from "node:assert/strict";

import {
  capabilities,
  normalizeExternalRows,
  pgvectorQueryValues,
  pineconeQueryBody,
  pineconeMatchesToRows,
  sqlIdentifier,
  vectorLiteral,
  withTypedFailure,
} from "../providers/node/lib.mjs";

const config = {
  packageName: "@zack/m13-reference-corpus",
  version: "0.1.0",
  corpus: "sha256:test-corpus",
  returnCitationsDefault: true,
};

test("capabilities advertise exact package corpus attestation", () => {
  assert.deepEqual(capabilities(config), {
    modes: ["vector_query"],
    features: ["citations"],
    packages: [
      {
        package: "@zack/m13-reference-corpus",
        version: "0.1.0",
        corpus: "sha256:test-corpus",
        ready: true,
      },
    ],
  });
});

test("pinecone metadata maps to normalized Knowledge results and citations", () => {
  const request = {
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
    return_citations: true,
  };
  const rows = pineconeMatchesToRows(
    [
      {
        id: "chunk_release_gate",
        score: 0.99,
        metadata: {
          package: "@zack/m13-reference-corpus",
          version: "0.1.0",
          corpus: "sha256:test-corpus",
          chunk_id: "chunk_release_gate",
          source_id: "src_ops_playbook",
          source_title: "Alpha Operations Playbook",
          source_uri: "agentpm://examples/m13/alpha-ops",
          text: "release gate",
        },
      },
    ],
    config,
  );
  assert.deepEqual(normalizeExternalRows(request, rows), {
    ok: true,
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
    results: [
      {
        rank: 1,
        score: 0.99,
        chunk_id: "chunk_release_gate",
        source_id: "src_ops_playbook",
        source_title: "Alpha Operations Playbook",
        source_uri: "agentpm://examples/m13/alpha-ops",
        text: "release gate",
        chunk_metadata: {
          package: "@zack/m13-reference-corpus",
          version: "0.1.0",
          corpus: "sha256:test-corpus",
          chunk_id: "chunk_release_gate",
          source_id: "src_ops_playbook",
          source_title: "Alpha Operations Playbook",
          source_uri: "agentpm://examples/m13/alpha-ops",
          text: "release gate",
        },
      },
    ],
    citations: [
      {
        chunk_id: "chunk_release_gate",
        source_id: "src_ops_playbook",
        title: "Alpha Operations Playbook",
        uri: "agentpm://examples/m13/alpha-ops",
      },
    ],
  });
});

test("omitted return_citations follows package retrieval default", () => {
  const request = {
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
  };
  const rows = [
    {
      score: 0.99,
      chunk_id: "chunk_release_gate",
      source_id: "src_ops_playbook",
      source_title: "Alpha Operations Playbook",
      source_uri: "agentpm://examples/m13/alpha-ops",
      text: "release gate",
      metadata: {},
    },
  ];
  assert.deepEqual(
    normalizeExternalRows(request, rows, { returnCitationsDefault: true })
      .citations,
    [
      {
        chunk_id: "chunk_release_gate",
        source_id: "src_ops_playbook",
        title: "Alpha Operations Playbook",
        uri: "agentpm://examples/m13/alpha-ops",
      },
    ],
  );
  assert.deepEqual(
    normalizeExternalRows(request, rows, { returnCitationsDefault: false })
      .citations,
    [],
  );
});

test("explicit return_citations false suppresses citations", () => {
  const request = {
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
    return_citations: false,
  };
  const rows = [
    {
      score: 0.99,
      chunk_id: "chunk_release_gate",
      source_id: "src_ops_playbook",
      source_title: "Alpha Operations Playbook",
      source_uri: "agentpm://examples/m13/alpha-ops",
      text: "release gate",
      metadata: {},
    },
  ];
  assert.deepEqual(
    normalizeExternalRows(request, rows, { returnCitationsDefault: true })
      .citations,
    [],
  );
});

test("score_threshold filters normalized rows before ranking and citations", () => {
  const request = {
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
    score_threshold: 0.8,
    return_citations: true,
  };
  const result = normalizeExternalRows(request, [
    {
      score: 0.79,
      chunk_id: "chunk_below",
      source_id: "src_ops_playbook",
      source_title: "Below Threshold",
      source_uri: "agentpm://examples/m13/below",
      text: "below",
      metadata: {},
    },
    {
      score: 0.95,
      chunk_id: "chunk_above",
      source_id: "src_ops_playbook",
      source_title: "Above Threshold",
      source_uri: "agentpm://examples/m13/above",
      text: "above",
      metadata: {},
    },
  ]);
  assert.deepEqual(
    result.results.map((row) => ({
      rank: row.rank,
      score: row.score,
      chunk_id: row.chunk_id,
    })),
    [{ rank: 1, score: 0.95, chunk_id: "chunk_above" }],
  );
  assert.deepEqual(result.citations, [
    {
      chunk_id: "chunk_above",
      source_id: "src_ops_playbook",
      title: "Above Threshold",
      uri: "agentpm://examples/m13/above",
    },
  ]);
});

test("pinecone query body maps top_k and fixed attestation filters", () => {
  assert.deepEqual(
    pineconeQueryBody(
      {
        package: "@zack/m13-reference-corpus",
        version: "0.1.0",
        mode: "vector_query",
        query: "alpha launch",
        top_k: 7,
        score_threshold: 0.8,
      },
      [0.1, 0.2, 0.3],
      config,
      "manual-namespace",
    ),
    {
      namespace: "manual-namespace",
      vector: [0.1, 0.2, 0.3],
      topK: 7,
      includeMetadata: true,
      filter: {
        package: { $eq: "@zack/m13-reference-corpus" },
        version: { $eq: "0.1.0" },
        corpus: { $eq: "sha256:test-corpus" },
      },
    },
  );
});

test("pgvector query values map vector, attestation filters, and top_k", () => {
  assert.deepEqual(
    pgvectorQueryValues(
      {
        package: "@zack/m13-reference-corpus",
        version: "0.1.0",
        mode: "vector_query",
        query: "alpha launch",
        top_k: 5,
      },
      [0.1, 0.2, -0.3],
      config,
    ),
    [
      "[0.1,0.2,-0.3]",
      "@zack/m13-reference-corpus",
      "0.1.0",
      "sha256:test-corpus",
      5,
    ],
  );
});

test("pgvector rows normalize to stable results and citations", () => {
  const request = {
    package: "@zack/m13-reference-corpus",
    version: "0.1.0",
    mode: "vector_query",
    query: "alpha launch",
    return_citations: true,
  };
  assert.deepEqual(
    normalizeExternalRows(request, [
      {
        score: 0.93,
        chunk_id: "chunk_pgvector",
        source_id: "src_pgvector",
        source_title: "pgvector Source",
        source_uri: "agentpm://examples/m13/pgvector",
        text: "pgvector row",
        metadata: { backend: "pgvector" },
      },
    ]),
    {
      ok: true,
      package: "@zack/m13-reference-corpus",
      version: "0.1.0",
      mode: "vector_query",
      query: "alpha launch",
      results: [
        {
          rank: 1,
          score: 0.93,
          chunk_id: "chunk_pgvector",
          source_id: "src_pgvector",
          source_title: "pgvector Source",
          source_uri: "agentpm://examples/m13/pgvector",
          text: "pgvector row",
          chunk_metadata: { backend: "pgvector" },
        },
      ],
      citations: [
        {
          chunk_id: "chunk_pgvector",
          source_id: "src_pgvector",
          title: "pgvector Source",
          uri: "agentpm://examples/m13/pgvector",
        },
      ],
    },
  );
});

test("pgvector SQL helpers reject unsafe identifiers and serialize vectors", () => {
  assert.equal(
    sqlIdentifier("agentpm_m13_knowledge_chunks"),
    "agentpm_m13_knowledge_chunks",
  );
  assert.equal(vectorLiteral([1, 0.5, -0.25]), "[1,0.5,-0.25]");
  assert.throws(() => sqlIdentifier("agentpm-m13"), /unsafe SQL identifier/);
  assert.throws(
    () => sqlIdentifier("chunks;drop_table"),
    /unsafe SQL identifier/,
  );
});

test("provider failures use typed Knowledge failure result shape", async () => {
  assert.deepEqual(
    await withTypedFailure(
      {
        package: "@zack/m13-reference-corpus",
        version: "0.1.0",
        mode: "vector_query",
        query: "alpha launch",
      },
      "pgvector_query_failed",
      async () => {
        throw new Error("database unavailable");
      },
    ),
    {
      ok: false,
      package: "@zack/m13-reference-corpus",
      version: "0.1.0",
      mode: "vector_query",
      query: "alpha launch",
      error: {
        code: "pgvector_query_failed",
        message: "database unavailable",
        retryable: false,
      },
    },
  );
});

test("pinecone metadata identity mismatch is rejected", () => {
  assert.throws(
    () =>
      pineconeMatchesToRows(
        [
          {
            id: "chunk_release_gate",
            score: 0.99,
            metadata: {
              package: "@zack/other",
              version: "0.1.0",
              corpus: "sha256:test-corpus",
            },
          },
        ],
        config,
      ),
    /mismatched package/,
  );
});
