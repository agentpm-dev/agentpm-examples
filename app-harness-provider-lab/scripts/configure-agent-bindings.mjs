import fs from 'node:fs';

const AGENT_PATH = 'agent.json';
const REASON_PHASE = 'reason';
const KNOWLEDGE_PACKAGES = ['@zack/agentpm-docs', '@zack/devwork-maintainer-guide'];
const MEMORY_PACKAGE = '@zack/support-customer-state';

const manifest = JSON.parse(fs.readFileSync(AGENT_PATH, 'utf8'));
manifest.bindings ??= {};
manifest.bindings.phases ??= {};
manifest.bindings.phases[REASON_PHASE] ??= {};

let changed = false;
const reason = manifest.bindings.phases[REASON_PHASE];

reason.knowledge ??= [];
for (const name of KNOWLEDGE_PACKAGES) {
  if (!reason.knowledge.includes(name)) {
    reason.knowledge.push(name);
    changed = true;
  }
}

reason.memory ??= [];
const existingMemory = reason.memory.find((entry) => entry.package === MEMORY_PACKAGE);
if (!existingMemory) {
  reason.memory.push({
    package: MEMORY_PACKAGE,
    spaces: ['customer_state'],
  });
  changed = true;
} else {
  existingMemory.spaces ??= [];
  for (const space of ['customer_state']) {
    if (!existingMemory.spaces.includes(space)) {
      existingMemory.spaces.push(space);
      changed = true;
    }
  }
}

if (changed) {
  fs.writeFileSync(`${AGENT_PATH}.tmp`, `${JSON.stringify(manifest, null, 2)}\n`);
  fs.renameSync(`${AGENT_PATH}.tmp`, AGENT_PATH);
  console.log('Configured provider lab Knowledge and Memory bindings for the reason phase.');
} else {
  console.log('Provider lab bindings are already configured.');
}
