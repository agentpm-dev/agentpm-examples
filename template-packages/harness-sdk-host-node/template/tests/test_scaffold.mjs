import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

test('scaffold includes the Harness SDK host files', () => {
  assert.ok(fs.existsSync('agentpm.harness.json'));
  assert.ok(fs.existsSync('src/main.ts'));
  assert.ok(fs.existsSync('reports/.gitkeep'));
});

test('Harness config uses host implementations for model, Hook, and approvals', () => {
  const config = JSON.parse(fs.readFileSync('agentpm.harness.json', 'utf8'));
  assert.equal(config.model.provider, 'node-host-model');
  assert.equal(config.providers.models['node-host-model'].implementation.type, 'host');
  assert.equal(config.hooks.implementations['sdk-before-model'].implementation.type, 'host');
  assert.equal(config.approvals.controller.implementation.type, 'host');
});
