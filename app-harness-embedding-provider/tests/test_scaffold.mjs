import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

test('scaffold includes the hosted embedding provider files', () => {
  assert.ok(fs.existsSync('agentpm.harness.json'));
  assert.ok(fs.existsSync('agentpm.sdk.harness.json'));
  assert.ok(fs.existsSync('src/main.ts'));
  assert.ok(fs.existsSync('runtime/openai-embedding-provider.mjs'));
  assert.ok(fs.existsSync('scripts/configure-agent-bindings.mjs'));
  assert.ok(fs.existsSync('reports/.gitkeep'));
});

test('standalone Harness config maps docs embeddings to the process provider', () => {
  const config = JSON.parse(fs.readFileSync('agentpm.harness.json', 'utf8'));
  const provider = config.providers.embeddings['local-openai-embeddings'];
  const match = config.knowledge.embedding_matches[0];

  assert.equal(config.model.provider, 'openai');
  assert.equal(provider.implementation.type, 'process');
  assert.equal(provider.implementation.command, 'node');
  assert.deepEqual(provider.implementation.args, ['runtime/openai-embedding-provider.mjs']);
  assert.equal(config.approvals, undefined);
  assert.deepEqual(match.match, {
    provider: 'openai',
    model: 'text-embedding-3-small',
    dimensions: 1536,
    normalized: true,
  });
  assert.equal(match.embedding_provider, 'local-openai-embeddings');
});

test('SDK Harness config maps docs embeddings to the host provider', () => {
  const config = JSON.parse(fs.readFileSync('agentpm.sdk.harness.json', 'utf8'));
  const provider = config.providers.embeddings['local-openai-embeddings'];
  const match = config.knowledge.embedding_matches[0];

  assert.equal(config.model.provider, 'openai');
  assert.equal(provider.implementation.type, 'host');
  assert.equal(config.approvals.controller.implementation.type, 'host');
  assert.deepEqual(match.match, {
    provider: 'openai',
    model: 'text-embedding-3-small',
    dimensions: 1536,
    normalized: true,
  });
  assert.equal(match.embedding_provider, 'local-openai-embeddings');
});

test('credentials stay out of the Harness config', () => {
  const standaloneConfigText = fs.readFileSync('agentpm.harness.json', 'utf8');
  const sdkConfigText = fs.readFileSync('agentpm.sdk.harness.json', 'utf8');
  assert.equal(standaloneConfigText.includes('sk-'), false);
  assert.equal(sdkConfigText.includes('sk-'), false);
  assert.equal(standaloneConfigText.toLowerCase().includes('secret'), false);
  assert.equal(sdkConfigText.toLowerCase().includes('secret'), false);
});
