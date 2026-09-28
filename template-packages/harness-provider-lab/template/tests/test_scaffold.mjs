import assert from 'node:assert/strict';
import fs from 'node:fs';
import { test } from 'node:test';

test('harness config wires all process provider bridges without literal secrets', () => {
  const config = JSON.parse(fs.readFileSync('agentpm.harness.json', 'utf8'));

  assert.equal(config.model.provider, 'provider-lab-model');
  assert.equal(config.providers.models['provider-lab-model'].implementation.type, 'process');
  assert.equal(config.providers.embeddings['local-openai-embeddings'].implementation.type, 'process');
  assert.equal(config.knowledge.runtimes['reference-knowledge'].implementation.type, 'process');
  assert.equal(config.memory.runtimes['reference-memory'].implementation.type, 'process');
  assert.equal(config.approvals.controller.implementation.type, 'process');

  const raw = JSON.stringify(config);
  assert.match(raw, /OPENAI_API_KEY/);
  assert.doesNotMatch(raw, /sk-[A-Za-z0-9]/);
  assert.doesNotMatch(raw, /password/i);
});

test('template runtime services exist', () => {
  for (const path of [
    'runtime/model-provider.mjs',
    'runtime/openai-embedding-provider.mjs',
    'runtime/reference-knowledge-runtime.mjs',
    'runtime/reference-memory-runtime.mjs',
    'runtime/approval-controller.mjs',
  ]) {
    assert.equal(fs.existsSync(path), true, `${path} should exist`);
  }
});
