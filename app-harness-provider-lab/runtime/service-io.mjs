import fs from 'node:fs';
import readline from 'node:readline';

export const SERVICE_PROTOCOL = 'agentpm-service';
export const SERVICE_VERSION = 1;

export async function serve(service, handlers) {
  loadLocalEnv();
  const input = readline.createInterface({ input: process.stdin });

  for await (const line of input) {
    if (!line.trim()) continue;
    let frame = { service };
    try {
      frame = JSON.parse(line);
      validateEnvelope(frame, service);

      if (frame.kind === 'initialize') {
        write(service, {
          kind: 'initialized',
          id: frame.id,
          result: await handlers.initialize(frame.payload ?? {}),
        });
        continue;
      }

      if (frame.kind !== 'request') {
        throw new Error(`unsupported service frame kind ${String(frame.kind)}`);
      }

      const handler = handlers[frame.method];
      if (typeof handler !== 'function') {
        throw new Error(`unsupported ${service} method ${String(frame.method)}`);
      }
      write(service, {
        kind: 'response',
        id: frame.id,
        result: await handler(frame.payload ?? {}),
      });
    } catch (error) {
      write(frame.service ?? service, {
        kind: 'error',
        id: frame.id,
        error: {
          code: `${service}_provider_error`,
          message: error instanceof Error ? error.message : String(error),
          retryable: false,
        },
      });
    }
  }
}

function validateEnvelope(frame, expectedService) {
  if (frame.protocol !== SERVICE_PROTOCOL) {
    throw new Error(`unsupported service protocol ${String(frame.protocol)}`);
  }
  if (frame.version !== SERVICE_VERSION) {
    throw new Error(`unsupported service protocol version ${String(frame.version)}`);
  }
  if (frame.service !== expectedService) {
    throw new Error(`unsupported service ${String(frame.service)}`);
  }
}

function write(service, frame) {
  process.stdout.write(
    `${JSON.stringify({
      protocol: SERVICE_PROTOCOL,
      version: SERVICE_VERSION,
      service,
      ...frame,
    })}\n`,
  );
}

export function loadLocalEnv() {
  if (!fs.existsSync('.env.local')) return;
  for (const rawLine of fs.readFileSync('.env.local', 'utf8').split(/\r?\n/)) {
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
