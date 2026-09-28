import { serve } from './service-io.mjs';

const REGISTRY_ID = 'local-openai-embeddings';
const EMBEDDING_PROVIDER = 'openai';
const EMBEDDING_MODEL = 'text-embedding-3-small';
const EMBEDDING_DIMENSIONS = 1536;
const EMBEDDING_NORMALIZED = true;

await serve('embedding', {
  initialize() {
    return {
      registry_id: REGISTRY_ID,
      ready: Boolean(process.env.OPENAI_API_KEY),
      embedding_spaces: [embeddingSpace()],
    };
  },
  async embed(payload) {
    validateEmbeddingRequest(payload);

    const baseUrl = (process.env.OPENAI_EMBEDDING_BASE_URL || 'https://api.openai.com/v1').replace(
      /\/+$/,
      '',
    );
    const response = await fetch(`${baseUrl}/embeddings`, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${requiredEnv('OPENAI_API_KEY')}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: EMBEDDING_MODEL,
        input: payload.text,
        dimensions: EMBEDDING_DIMENSIONS,
      }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`OpenAI embeddings request failed: ${response.status} ${body}`);
    }

    const result = await response.json();
    const vector = result.data?.[0]?.embedding;
    if (!Array.isArray(vector)) {
      throw new Error('OpenAI embeddings response did not include data[0].embedding');
    }
    if (vector.length !== EMBEDDING_DIMENSIONS) {
      throw new Error(
        `OpenAI embeddings returned ${vector.length} dimensions; expected ${EMBEDDING_DIMENSIONS}`,
      );
    }

    return {
      vector,
      provider: EMBEDDING_PROVIDER,
      model: EMBEDDING_MODEL,
      dimensions: EMBEDDING_DIMENSIONS,
      normalized: EMBEDDING_NORMALIZED,
    };
  },
});

function validateEmbeddingRequest(request) {
  if (
    request.provider !== EMBEDDING_PROVIDER ||
    request.model !== EMBEDDING_MODEL ||
    request.dimensions !== EMBEDDING_DIMENSIONS ||
    request.normalized !== EMBEDDING_NORMALIZED
  ) {
    throw new Error(
      `Unsupported embedding request ${request.provider}/${request.model}/${request.dimensions}/${request.normalized}`,
    );
  }
  if (typeof request.text !== 'string' || request.text.length === 0) {
    throw new Error('Embedding request requires non-empty text');
  }
}

function embeddingSpace() {
  return {
    provider: EMBEDDING_PROVIDER,
    model: EMBEDDING_MODEL,
    dimensions: EMBEDDING_DIMENSIONS,
    normalized: EMBEDDING_NORMALIZED,
  };
}

function requiredEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required. Add it to .env.local or export it before running.`);
  }
  return value;
}
