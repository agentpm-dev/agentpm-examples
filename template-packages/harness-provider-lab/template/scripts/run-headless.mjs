import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

loadLocalEnv();

const agentpm = process.env.AGENTPM || 'agentpm';
const args = process.argv.slice(2);
if (args[0] === '--') args.shift();
const input =
  args.join(' ') ||
  'Use the provider lab to verify every configured provider bridge.';
fs.mkdirSync('reports', { recursive: true });
const reportPath = 'reports/provider-lab-report.json';

const result = spawnSync(
  agentpm,
  ['harness', '--headless', '--input', input, '--report', reportPath],
  { stdio: 'inherit', env: process.env },
);

process.exit(result.status ?? 1);

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
