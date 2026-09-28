import 'dotenv/config';
import { HarnessClient, type HarnessEvent, type HarnessJsonValue } from '@agentpm/sdk';

const cwd = process.cwd();
const args = process.argv.slice(2);
const preflightOnly = args.includes('--preflight-only');
const prompt =
  args.filter((arg) => arg !== '--preflight-only').join(' ').trim() ||
  'Use the SDK-hosted Harness example to inspect this generated workspace.';
const agentpmPath = process.env.AGENTPM || 'agentpm';
const userScope = process.env.SDK_HOST_USER || 'node-sdk-user';

const callbacks: string[] = [];
let modelCalls = 0;
let shuttingDown = false;

const client = new HarnessClient({
  agentpmPath,
  cwd,
  configPath: 'agentpm.harness.json',
  scopes: {
    user: userScope,
  },
});

client.onStderr((chunk) => {
  process.stderr.write(chunk);
});

client.onEvent((event: HarnessEvent) => {
  if (interestingEvent(event)) {
    const run = event.run_id ? ` ${event.run_id}` : '';
    console.log(`[event] ${event.event_type}${run}`);
  }
});

client
  .registerModelProvider(
    'node-host-model',
    // Replace this deterministic provider with your internal model gateway.
    (payload) => {
      const request = isRecord(payload) && isRecord(payload.request) ? payload.request : {};
      return hostModel(request);
    },
    {
      model: 'deterministic-node-host',
      context_window_tokens: 8000,
    },
  )
  .onBeforeModelRequest(
    (input) => {
      const phase = phaseId(input as Record<string, HarnessJsonValue>);
      callbacks.push(`before_model_request:${phase}`);
      return {
        decision: 'continue',
        patch: {
          // Attach request-scoped UI, API, policy, or service context here.
          context_sections: [
            {
              title: 'Node SDK host note',
              content:
                'This run is using a Node-hosted model provider, Hook, and approval callback.',
            },
          ],
        },
      };
    },
    { registryId: 'sdk-before-model' },
  )
  .onApproval((request) => {
    const checkpoint =
      typeof request === 'object' && request && 'checkpoint' in request
        ? (request.checkpoint as Record<string, HarnessJsonValue>)
        : undefined;
    callbacks.push(`approval:${String(checkpoint?.id ?? 'unknown')}`);
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
  if (status !== 'ready' && status !== 'ready_with_warnings') {
    console.log(JSON.stringify(preflightDiagnostics(preflight, session), null, 2));
  }
  if (preflightOnly) {
    const registrations = client.hostServiceRegistrations();
    console.log(`Host services: ${registrations.length}`);
    for (const registration of registrations) {
      console.log(
        `- ${registration.service.role}:${registration.service.registry_id} active=${registration.active}`,
      );
    }
  } else {
    // A web route, queue worker, or CLI command can call this same run boundary.
    const result = await client.run(prompt, {
      metadata: {
        source: 'harness-sdk-host-node-template',
      },
    });

    const report = result.report as Record<string, HarnessJsonValue> | undefined;
    console.log(`Run terminal status: ${String(result.status ?? report?.terminal_status ?? 'unknown')}`);
    console.log(`Callbacks: ${callbacks.join(', ') || 'none'}`);
    console.log(`Model calls: ${modelCalls}`);
    console.log(`Report returned: ${report ? 'yes' : 'no'}`);
    console.log(`Trace path: ${String(report?.trace_path ?? 'not reported')}`);
  }
} finally {
  await client.shutdown().catch(() => undefined);
}

function hostModel(request: Record<string, HarnessJsonValue>): Record<string, HarnessJsonValue> {
  modelCalls += 1;
  const phase = phaseId(request);

  if (phase === 'reason') {
    return completion('reason-complete', 'act', {
      summary:
        'The Node SDK host app is ready to proceed. It registered a host model provider, before-model Hook, and approval controller.',
      next: 'Proceed to the approved act phase.',
    });
  }

  if (phase === 'act') {
    return {
      id: `node-host-act-${modelCalls}`,
      assistant_content:
        'The approved action phase ran through the Node SDK host. No external side effect was needed for this scaffold.',
      actions: [],
      usage: usage(),
      finish_reason: 'stop',
      provider_metadata: { template: 'harness-sdk-host-node', phase },
    };
  }

  return completion('reflect-complete', 'complete', {
    summary:
      'The run completed through the Node SDK machine host with events, usage, checkpoint approval, and report generation.',
  });
}

function completion(id: string, outcome: string, output: Record<string, string>) {
  return {
    id: `${id}-${modelCalls}`,
    assistant_content: null,
    actions: [
      {
        id: `${id}-action-${modelCalls}`,
        action: {
          type: 'phase_completion',
          outcome,
          output,
        },
      },
    ],
    usage: usage(),
    finish_reason: 'tool_calls',
    provider_metadata: { template: 'harness-sdk-host-node', outcome },
  };
}

function usage() {
  return {
    input_tokens: 120,
    output_tokens: 36,
    total_tokens: 156,
  };
}

function phaseId(value: Record<string, HarnessJsonValue>): string {
  const phase = value.phase;
  if (isRecord(phase) && typeof phase.phase_id === 'string') return phase.phase_id;
  if (isRecord(phase) && typeof phase.id === 'string') return phase.id;
  if (typeof value.phase_id === 'string') return value.phase_id;
  return modelCalls <= 1 ? 'reason' : modelCalls === 2 ? 'act' : 'reflect';
}

function isRecord(value: unknown): value is Record<string, HarnessJsonValue> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function interestingEvent(event: HarnessEvent): boolean {
  if (typeof event.event_type !== 'string') return false;
  return [
    'run_started',
    'phase_started',
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
