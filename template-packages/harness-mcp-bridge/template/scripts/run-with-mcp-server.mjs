import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';

loadLocalEnv();

let command = process.argv.slice(2);
if (command[0] === '--') command = command.slice(1);
if (command.length === 0) {
  console.error('Usage: node scripts/run-with-mcp-server.mjs -- <command> [args...]');
  process.exit(2);
}
if (command[0] === 'agentpm') {
  command[0] = process.env.AGENTPM || 'agentpm';
}

const server = spawn(process.execPath, ['runtime/local-mcp-server.mjs'], {
  stdio: ['ignore', 'ignore', 'inherit'],
  env: process.env,
});

const shutdown = () => {
  if (!server.killed) server.kill();
};
process.on('exit', shutdown);
process.on('SIGINT', () => {
  shutdown();
  process.exit(130);
});
process.on('SIGTERM', () => {
  shutdown();
  process.exit(143);
});

try {
  await waitForHealth();
  const result = spawnSync(command[0], command.slice(1), {
    stdio: 'inherit',
    env: process.env,
  });
  process.exit(result.status ?? 1);
} finally {
  shutdown();
}

async function waitForHealth() {
  const port = Number(process.env.MCP_BRIDGE_PORT || '18241');
  const url = `http://127.0.0.1:${port}/health`;
  const started = Date.now();
  while (Date.now() - started < 5000) {
    if (server.exitCode !== null) {
      throw new Error(`MCP fixture exited with code ${server.exitCode}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Keep polling until the fixture server is listening.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function loadLocalEnv() {
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
