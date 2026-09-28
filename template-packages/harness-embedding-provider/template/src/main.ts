import 'dotenv/config';
import {
  HarnessClient,
  type EmbeddingProviderRequest,
  type HarnessEvent,
  type HarnessJsonValue,
} from '@agentpm/sdk';

const EMBEDDING_PROVIDER_ID = 'local-openai-embeddings';
const EMBEDDING_PROVIDER = 'openai';
const EMBEDDING_MODEL = 'text-embedding-3-small';
const EMBEDDING_DIMENSIONS = 1536;
const EMBEDDING_NORMALIZED = true;

const cwd = process.cwd();
const args = process.argv.slice(2);
const preflightOnly = args.includes('--preflight-only');
const prompt =
  args.filter((arg) => arg !== '--preflight-only').join(' ').trim() ||
  'Use the AgentPM docs Knowledge package to explain how Harness SDK-hosted providers work.';
const agentpmPath = process.env.AGENTPM || 'agentpm';
const userScope = process.env.SDK_HOST_USER || '{{ default_user_scope }}';

let embeddingRequests = 0;
let knowledgeEvents = 0;
let approvals = 0;
let shuttingDown = false;

const client = new HarnessClient({
  agentpmPath,
  cwd,
  configPath: 'agentpm.sdk.harness.json',
  scopes: {
    user: userScope,
  },
});

client.onStderr((chunk) => {
  process.stderr.write(chunk);
});

client.onEvent((event: HarnessEvent) => {
  if (typeof event.event_type !== 'string') return;
  if (event.event_type.includes('knowledge')) knowledgeEvents += 1;
  if (interestingEvent(event)) {
    const run = event.run_id ? ` ${event.run_id}` : '';
    console.log(`[event] ${event.event_type}${run}`);
  }
});

client
  .registerEmbeddingProvider(EMBEDDING_PROVIDER_ID, embedWithOpenAI, {
    embedding_spaces: [
      {
        provider: EMBEDDING_PROVIDER,
        model: EMBEDDING_MODEL,
        dimensions: EMBEDDING_DIMENSIONS,
        normalized: EMBEDDING_NORMALIZED,
      },
    ],
  })
  .onApproval((request) => {
    approvals += 1;
    const checkpoint =
      isRecord(request) && isRecord(request.checkpoint)
        ? String(request.checkpoint.id ?? 'unknown')
        : 'unknown';
    console.log(`[approval] approving checkpoint ${checkpoint}`);
    return 'approve';
  });

process.on('SIGINT', () => {
  if (shuttingDown) return;
  shuttingDown = true;
  void (async () => {
    try {
      await client.cancelRun();
    } catch {
      // The process may already be terminal; shutdown below is still safe.
    }
    await client.shutdown().catch(() => undefined);
    process.exit(130);
  })();
});

try {
  const session = await client.initialize();
  printSession(session);

  const preflight = await client.preflight();
  const status = knownOr(preflightStatus(preflight), preflightStatus(session));
  console.log(`Preflight status: ${status}`);
  printHostServices();

  if (status !== 'ready' && status !== 'ready_with_warnings') {
    console.log(JSON.stringify(preflightDiagnostics(preflight, session), null, 2));
  }

  if (!preflightOnly) {
    requireOpenAiKey();
    const result = await client.run(prompt, {
      metadata: {
        source: 'harness-embedding-provider-template',
      },
    });

    const report = result.report as Record<string, HarnessJsonValue> | undefined;
    console.log(`Run terminal status: ${String(result.status ?? report?.terminal_status ?? 'unknown')}`);
    console.log(`Embedding requests: ${embeddingRequests}`);
    console.log(`Knowledge events: ${knowledgeEvents}`);
    console.log(`Approvals: ${approvals}`);
    console.log(`Report returned: ${report ? 'yes' : 'no'}`);
    console.log(`Trace path: ${String(report?.trace_path ?? 'not reported')}`);
  }
} finally {
  await client.shutdown().catch(() => undefined);
}

async function embedWithOpenAI(request: EmbeddingProviderRequest) {
  validateEmbeddingRequest(request);
  embeddingRequests += 1;

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

  const payload = (await response.json()) as OpenAIEmbeddingResponse;
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

function validateEmbeddingRequest(request: EmbeddingProviderRequest): void {
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
}

function requireOpenAiKey(): void {
  requiredEnv('OPENAI_API_KEY');
}

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required. Add it to .env.local or export it before running.`);
  }
  return value;
}

function printHostServices(): void {
  const registrations = client.hostServiceRegistrations();
  console.log(`Host services: ${registrations.length}`);
  for (const registration of registrations) {
    console.log(
      `- ${registration.service.role}:${registration.service.registry_id} active=${registration.active}`,
    );
  }
}

function interestingEvent(event: HarnessEvent): boolean {
  if (typeof event.event_type !== 'string') return false;
  return [
    'run_started',
    'phase_started',
    'knowledge_surface_ready',
    'knowledge_request_started',
    'knowledge_retrieved',
    'knowledge_failed',
    'approval_requested',
    'approval_approved',
    'phase_result_ready',
    'run_completed',
  ].includes(event.event_type);
}

function sessionId(session: Record<string, unknown>): string {
  const nested = session.session;
  if (isRecord(nested) && typeof nested.session_id === 'string') return nested.session_id;
  return typeof session.session_id === 'string' ? session.session_id : 'unknown';
}

function printSession(session: Record<string, unknown>): void {
  const id = sessionId(session);
  console.log(id === 'unknown' ? 'Harness session initialized' : `Harness session ${id}`);
}

function preflightStatus(preflight: Record<string, HarnessJsonValue | undefined>): string {
  const nested = preflight.preflight;
  if (isRecord(nested) && typeof nested.status === 'string') return nested.status;
  return typeof preflight.status === 'string' ? preflight.status : 'unknown';
}

function preflightDiagnostics(
  preflight: Record<string, HarnessJsonValue | undefined>,
  fallback: Record<string, unknown>,
) {
  const nested = preflight.preflight;
  if (isRecord(nested) && Array.isArray(nested.diagnostics)) return nested.diagnostics;
  if (Array.isArray(preflight.diagnostics)) return preflight.diagnostics;
  const fallbackNested = fallback.preflight;
  if (isRecord(fallbackNested) && Array.isArray(fallbackNested.diagnostics)) {
    return fallbackNested.diagnostics;
  }
  return [];
}

function knownOr(current: string, fallback: string): string {
  return current === 'unknown' ? fallback : current;
}

function isRecord(value: unknown): value is Record<string, HarnessJsonValue> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

type OpenAIEmbeddingResponse = {
  data?: Array<{
    embedding?: number[];
  }>;
};
