import {
  assertAttestedRequest,
  capabilities,
  normalizeExternalRows,
  pineconeQueryBody,
  pineconeMatchesToRows,
  providerConfig,
  withTypedFailure,
} from "./lib.mjs";

const { serveKnowledgeRuntimeProcess } = await import("@agentpm/sdk");
if (typeof serveKnowledgeRuntimeProcess !== "function") {
  throw new Error(
    "Installed @agentpm/sdk does not export serveKnowledgeRuntimeProcess. Install a newer SDK release, or build and link the local agentpm-sdk-node checkout for pre-publish milestone testing.",
  );
}

const config = providerConfig("pinecone-reference");

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

async function embedQuery(text) {
  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${requireEnv("OPENAI_API_KEY")}`,
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
  return withTypedFailure(request, "pinecone_query_failed", async () => {
    assertAttestedRequest(request, config);
    const vector = await embedQuery(request.query);
    const response = await fetch(
      `${requireEnv("PINECONE_INDEX_HOST").replace(/\/$/, "")}/query`,
      {
        method: "POST",
        headers: {
          "Api-Key": requireEnv("PINECONE_API_KEY"),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          pineconeQueryBody(
            request,
            vector,
            config,
            process.env.PINECONE_NAMESPACE || "",
          ),
        ),
      },
    );
    if (!response.ok) {
      throw new Error(`Pinecone query failed with HTTP ${response.status}`);
    }
    const payload = await response.json();
    return normalizeExternalRows(
      request,
      pineconeMatchesToRows(
        Array.isArray(payload.matches) ? payload.matches : [],
        config,
      ),
      { returnCitationsDefault: config.returnCitationsDefault },
    );
  });
}

await serveKnowledgeRuntimeProcess(
  config.runtimeId,
  retrieve,
  capabilities(config),
);
