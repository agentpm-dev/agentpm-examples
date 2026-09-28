import fs from 'node:fs';

const AGENT_PATH = 'agent.json';
const KNOWLEDGE_PACKAGE = '@zack/agentpm-docs';
const PHASES = ['reason'];

const manifest = JSON.parse(fs.readFileSync(AGENT_PATH, 'utf8'));
manifest.bindings ??= {};
manifest.bindings.phases ??= {};

let changed = false;
for (const phase of PHASES) {
  manifest.bindings.phases[phase] ??= {};
  manifest.bindings.phases[phase].knowledge ??= [];
  if (!manifest.bindings.phases[phase].knowledge.includes(KNOWLEDGE_PACKAGE)) {
    manifest.bindings.phases[phase].knowledge.push(KNOWLEDGE_PACKAGE);
    changed = true;
  }
}

if (changed) {
  fs.writeFileSync(`${AGENT_PATH}.tmp`, `${JSON.stringify(manifest, null, 2)}\n`);
  fs.renameSync(`${AGENT_PATH}.tmp`, AGENT_PATH);
  console.log(`Configured ${KNOWLEDGE_PACKAGE} Knowledge bindings for ${PHASES.join(', ')}.`);
}
