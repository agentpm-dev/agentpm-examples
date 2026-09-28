import assert from 'node:assert/strict';
import fs from 'node:fs';
import { test } from 'node:test';

test('harness config uses scoped HTTP MCP import with env-projected credential', () => {
  const config = JSON.parse(fs.readFileSync('agentpm.harness.json', 'utf8'));
  const imported = config.mcp.imports['bridge-search'];

  assert.equal(imported.transport, 'http');
  assert.equal(imported.url, 'http://127.0.0.1:18241/mcp');
  assert.deepEqual(imported.headers.Authorization, { env: 'MCP_BRIDGE_AUTHORIZATION' });
  assert.equal(imported.scope.mode, 'phases');
  assert.deepEqual(imported.scope.phases, ['act']);
  assert.deepEqual(imported.tools, ['lookup']);
  assert.equal(config.mcp.exports.enabled, true);

  const raw = JSON.stringify(config);
  assert.doesNotMatch(raw, /local-mcp-bridge-token/);
  assert.doesNotMatch(raw, /Bearer\s+\w/);
});

test('runtime and setup scripts exist', () => {
  for (const path of [
    'runtime/local-mcp-server.mjs',
    'runtime/model-provider.mjs',
    'runtime/approval-controller.mjs',
    'scripts/configure-agent-bindings.mjs',
    'scripts/run-with-mcp-server.mjs',
    'scripts/run-headless.mjs',
  ]) {
    assert.equal(fs.existsSync(path), true, `${path} should exist`);
  }
});
