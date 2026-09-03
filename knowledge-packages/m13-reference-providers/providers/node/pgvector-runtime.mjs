import pg from "pg";

import {
  assertAttestedRequest,
  capabilities,
  normalizeExternalRows,
  pgvectorQueryValues,
  providerConfig,
  sqlIdentifier,
  withTypedFailure,
} from "./lib.mjs";

const { serveKnowledgeRuntimeProcess } = await import("@agentpm/sdk");
if (typeof serveKnowledgeRuntimeProcess !== "function") {
  throw new Error(
    "Installed @agentpm/sdk does not export serveKnowledgeRuntimeProcess. Install a newer SDK release, or build and link the local agentpm-sdk-node checkout for pre-publish milestone testing.",
  );
}

const config = providerConfig("pgvector-reference");
const table = sqlIdentifier(
  process.env.PGVECTOR_TABLE || "agentpm_m13_knowledge_chunks",
);
const pool = new pg.Pool({
  connectionString: process.env.PGVECTOR_DATABASE_URL,
});

async function embedQuery(text) {
  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY || ""}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: config.embeddingModel, input: text }),
  });
  if (!response.ok) {
    throw new Error(
      `OpenAI embedding request failed with HTTP ${response.status}`,
    );
  }
  const payload = await response.json();
  const vector = payload.data?.[0]?.embedding;
  if (!Array.isArray(vector) || vector.length !== config.dimensions) {
    throw new Error(
      `OpenAI embedding dimensions did not match ${config.dimensions}`,
    );
  }
  return vector;
}

async function retrieve(request) {
  return withTypedFailure(request, "pgvector_query_failed", async () => {
    assertAttestedRequest(request, config);
    if (!process.env.PGVECTOR_DATABASE_URL) {
      throw new Error("PGVECTOR_DATABASE_URL is required");
    }
    if (!process.env.OPENAI_API_KEY) {
      throw new Error("OPENAI_API_KEY is required");
    }
    const vector = await embedQuery(request.query);
    const result = await pool.query(
      `
      SELECT
        chunk_id,
        source_id,
        source_title,
        source_uri,
        text,
        metadata,
        1 - (embedding <=> $1::vector) AS score
      FROM ${table}
      WHERE package_name = $2
        AND package_version = $3
        AND corpus_hash = $4
      ORDER BY embedding <=> $1::vector
      LIMIT $5
      `,
      pgvectorQueryValues(request, vector, config),
    );
    return normalizeExternalRows(request, result.rows, {
      returnCitationsDefault: config.returnCitationsDefault,
    });
  });
}

await serveKnowledgeRuntimeProcess(
  config.runtimeId,
  retrieve,
  capabilities(config),
);
