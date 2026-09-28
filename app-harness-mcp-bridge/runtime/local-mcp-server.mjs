import http from 'node:http';
import { loadLocalEnv } from './service-io.mjs';

loadLocalEnv();

const port = Number(process.env.MCP_BRIDGE_PORT || '18241');
const expectedAuthorization = process.env.MCP_BRIDGE_AUTHORIZATION || '';

const server = http.createServer(async (request, response) => {
  if (request.method === 'GET' && request.url === '/health') {
    writeJson(response, 200, { ok: true });
    return;
  }

  if (request.method !== 'POST' || !['/', '/mcp'].includes(request.url || '')) {
    writeJson(response, 404, { error: 'not found' });
    return;
  }

  if (expectedAuthorization) {
    const actual = request.headers.authorization || '';
    if (actual !== expectedAuthorization) {
      writeJson(response, 401, {
        jsonrpc: '2.0',
        id: null,
        error: { code: -32001, message: 'unauthorized MCP bridge request' },
      });
      return;
    }
  }

  let body;
  try {
    body = JSON.parse(await readBody(request));
  } catch {
    writeJson(response, 400, {
      jsonrpc: '2.0',
      id: null,
      error: { code: -32700, message: 'invalid JSON' },
    });
    return;
  }

  const result = handleJsonRpc(body);
  writeJson(response, 200, {
    jsonrpc: '2.0',
    id: body.id ?? null,
    result,
  });
});

server.listen(port, '127.0.0.1', () => {
  console.error(`MCP bridge fixture listening on http://127.0.0.1:${port}/mcp`);
});

function handleJsonRpc(request) {
  switch (request.method) {
    case 'initialize':
      return {
        protocolVersion: '2025-06-18',
        serverInfo: {
          name: 'agentpm-harness-mcp-bridge-fixture',
          version: '0.1.0',
        },
      };
    case 'tools/list':
      return {
        tools: [
          {
            name: 'lookup',
            description: 'Lookup bridge context for a Harness MCP import demo.',
            inputSchema: {
              type: 'object',
              additionalProperties: false,
              properties: {
                query: {
                  type: 'string',
                  description: 'Lookup query.',
                },
                include_context: {
                  type: 'boolean',
                  description: 'Whether to include explanatory context.',
                },
              },
              required: ['query'],
            },
          },
        ],
      };
    case 'tools/call': {
      const args = request.params?.arguments || {};
      return {
        content: [
          {
            type: 'text',
            text: `lookup ok: ${String(args.query || '')}`,
          },
        ],
        structuredContent: {
          ok: true,
          query: args.query || '',
          import_scope: 'act',
          context: args.include_context
            ? 'This result came from the local HTTP MCP import fixture.'
            : undefined,
        },
        isError: false,
      };
    }
    default:
      return {};
  }
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let data = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => {
      data += chunk;
    });
    request.on('end', () => resolve(data));
    request.on('error', reject);
  });
}

function writeJson(response, statusCode, value) {
  const body = JSON.stringify(value);
  response.writeHead(statusCode, {
    'content-type': 'application/json',
    'content-length': Buffer.byteLength(body),
  });
  response.end(body);
}
