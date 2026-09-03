export function providerConfig(defaultRuntimeId) {
  const returnCitationsDefault = process.env.AGENTPM_KNOWLEDGE_RETURN_CITATIONS;
  return {
    runtimeId: process.env.AGENTPM_KNOWLEDGE_RUNTIME_ID || defaultRuntimeId,
    packageName:
      process.env.AGENTPM_KNOWLEDGE_PACKAGE || "@zack/m13-reference-corpus",
    version: process.env.AGENTPM_KNOWLEDGE_VERSION || "0.1.0",
    corpus: process.env.AGENTPM_KNOWLEDGE_CORPUS_HASH || "",
    embeddingProvider: process.env.AGENTPM_EMBEDDING_PROVIDER || "openai",
    embeddingModel:
      process.env.AGENTPM_EMBEDDING_MODEL || "text-embedding-3-small",
    dimensions: Number(process.env.AGENTPM_EMBEDDING_DIMENSIONS || "1536"),
    returnCitationsDefault:
      returnCitationsDefault === undefined
        ? true
        : returnCitationsDefault.toLowerCase() !== "false",
  };
}

export function capabilities(config) {
  return {
    modes: ["vector_query"],
    features: ["citations"],
    packages: [
      {
        package: config.packageName,
        version: config.version,
        corpus: config.corpus,
        ready: Boolean(config.corpus),
      },
    ],
  };
}

export function assertAttestedRequest(request, config) {
  if (request.package !== config.packageName) {
    throw new Error(
      `request package ${request.package} does not match ${config.packageName}`,
    );
  }
  if (request.version !== config.version) {
    throw new Error(
      `request version ${request.version} does not match ${config.version}`,
    );
  }
  if (request.mode !== "vector_query") {
    throw new Error(`unsupported Knowledge mode ${request.mode}`);
  }
  if (!request.query || typeof request.query !== "string") {
    throw new Error("vector_query request requires query");
  }
  if (!config.corpus) {
    throw new Error(
      "AGENTPM_KNOWLEDGE_CORPUS_HASH is required for package attestation",
    );
  }
}

export function failureResult(request, code, message) {
  return {
    ok: false,
    package: request.package,
    version: request.version,
    mode: request.mode,
    query: request.query,
    error: { code, message, retryable: false },
  };
}

export async function withTypedFailure(request, code, operation) {
  try {
    return await operation();
  } catch (error) {
    return failureResult(request, code, error.message);
  }
}

export function requestTopK(request, defaultTopK = 3) {
  return Number.isInteger(request.top_k) && request.top_k > 0
    ? request.top_k
    : defaultTopK;
}

export function pineconeQueryBody(request, vector, config, namespace = "") {
  return {
    namespace,
    vector,
    topK: requestTopK(request),
    includeMetadata: true,
    filter: {
      package: { $eq: config.packageName },
      version: { $eq: config.version },
      corpus: { $eq: config.corpus },
    },
  };
}

export function sqlIdentifier(value) {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(value)) {
    throw new Error(`unsafe SQL identifier ${value}`);
  }
  return value;
}

export function vectorLiteral(vector) {
  return `[${vector.join(",")}]`;
}

export function pgvectorQueryValues(request, vector, config) {
  const literal = vectorLiteral(vector);
  return [
    literal,
    config.packageName,
    config.version,
    config.corpus,
    requestTopK(request),
  ];
}

export function normalizeExternalRows(request, rows, options = {}) {
  const threshold =
    typeof request.score_threshold === "number"
      ? request.score_threshold
      : undefined;
  const results = rows
    .map((row) => {
      const metadata = row.metadata || {};
      const result = {
        rank: 0,
        score: Number(row.score ?? 0),
        chunk_id: String(row.chunk_id || metadata.chunk_id),
        source_id: String(row.source_id || metadata.source_id),
        chunk_metadata: metadata.chunk_metadata || metadata,
      };
      const sourceTitle =
        row.source_title || metadata.source_title || metadata.title;
      const sourceUri = row.source_uri || metadata.source_uri || metadata.uri;
      const text = row.text || metadata.text;
      if (sourceTitle) result.source_title = sourceTitle;
      if (sourceUri) result.source_uri = sourceUri;
      if (text) result.text = text;
      if (metadata.source_metadata)
        result.source_metadata = metadata.source_metadata;
      return result;
    })
    .filter((result) => threshold === undefined || result.score >= threshold)
    .map((result, index) => ({ ...result, rank: index + 1 }));
  const includeCitations =
    request.return_citations ?? options.returnCitationsDefault ?? true;
  return {
    ok: true,
    package: request.package,
    version: request.version,
    mode: request.mode,
    query: request.query,
    results,
    citations: includeCitations
      ? results.map((result) => ({
          chunk_id: result.chunk_id,
          source_id: result.source_id,
          title: result.source_title,
          uri: result.source_uri,
        }))
      : [],
  };
}

export function pineconeMatchesToRows(matches, config) {
  return matches.map((match) => {
    const metadata = match.metadata || {};
    if (metadata.package !== config.packageName) {
      throw new Error(
        `Pinecone match ${match.id} has mismatched package metadata`,
      );
    }
    if (metadata.version !== config.version) {
      throw new Error(
        `Pinecone match ${match.id} has mismatched version metadata`,
      );
    }
    if (metadata.corpus !== config.corpus) {
      throw new Error(
        `Pinecone match ${match.id} has mismatched corpus metadata`,
      );
    }
    return {
      score: match.score,
      chunk_id: metadata.chunk_id || match.id,
      source_id: metadata.source_id,
      source_title: metadata.source_title,
      source_uri: metadata.source_uri,
      text: metadata.text,
      metadata,
    };
  });
}
