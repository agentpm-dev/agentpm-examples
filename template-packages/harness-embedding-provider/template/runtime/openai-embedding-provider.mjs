import fs from 'node:fs';
import readline from 'node:readline';

const SERVICE_PROTOCOL = 'agentpm-service';
const SERVICE_VERSION = 1;
const REGISTRY_ID = 'local-openai-embeddings';
const EMBEDDING_PROVIDER = 'openai';
const EMBEDDING_MODEL = 'text-embedding-3-small';
const EMBEDDING_DIMENSIONS = 1536;
const EMBEDDING_NORMALIZED = true;

loadLocalEnv();

const input = readline.createInterface({ input: process.stdin });

for await (const line of input) {
  if (!line.trim()) continue;
  let frame = { service: 'embedding' };
  try {
    frame = JSON.parse(line);
    validateEnvelope(frame);

    if (frame.kind === 'initialize') {
      write({
        kind: 'initialized',
        id: frame.id,
        service: 'embedding',
        result: {
          registry_id: REGISTRY_ID,
          ready: Boolean(process.env.OPENAI_API_KEY),
          embedding_spaces: [embeddingSpace()],
        },
      });
      continue;
    }

    if (frame.kind !== 'request') {
      throw new Error(`unsupported service frame kind ${String(frame.kind)}`);
    }
    if (frame.method !== 'embed') {
      throw new Error(`Unsupported EmbeddingProvider method ${String(frame.method)}`);
    }

    write({
      kind: 'response',
      id: frame.id,
      service: 'embedding',
      result: await embedWithOpenAI(frame.payload ?? {}),
    });
  } catch (error) {
    write({
      kind: 'error',
      id: frame.id,
      service: frame.service ?? 'embedding',
      error: {
        code: 'embedding_provider_error',
        message: error instanceof Error ? error.message : String(error),
        retryable: false,
      },
    });
  }
}

function validateEnvelope(frame) {
  if (frame.protocol !== SERVICE_PROTOCOL) {
    throw new Error(`unsupported service protocol ${String(frame.protocol)}`);
  }
  if (frame.version !== SERVICE_VERSION) {
    throw new Error(`unsupported service protocol version ${String(frame.version)}`);
  }
  if (frame.service !== 'embedding') {
    throw new Error(`unsupported service ${String(frame.service)}`);
  }
}

async function embedWithOpenAI(request) {
  validateEmbeddingRequest(request);

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
      input: request.text,
      dimensions: EMBEDDING_DIMENSIONS,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenAI embeddings request failed: ${response.status} ${body}`);
  }

  const payload = await response.json();
  const vector = payload.data?.[0]?.embedding;
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
}

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

function write(frame) {
  process.stdout.write(
    `${JSON.stringify({
      protocol: SERVICE_PROTOCOL,
      version: SERVICE_VERSION,
      ...frame,
    })}\n`,
  );
}

function loadLocalEnv() {
  if (!fs.existsSync('.env.local')) return;
  const lines = fs.readFileSync('.env.local', 'utf8').split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const separator = line.indexOf('=');
    if (separator <= 0) continue;
    const key = line.slice(0, separator).trim();
    if (process.env[key]) continue;
    process.env[key] = unquote(line.slice(separator + 1).trim());
  }
}

function unquote(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}
