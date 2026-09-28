import fs from 'node:fs';

const AGENT_PATH = 'agent.json';
const EXPORT_ID = 'authored-tools';
const EXPORT_TOOLS = ['@zack/csv-query', '@zack/json-transform'];

const manifest = JSON.parse(fs.readFileSync(AGENT_PATH, 'utf8'));
manifest.bindings ??= {};
manifest.bindings.mcp ??= [];

let changed = false;
let exportSurface = manifest.bindings.mcp.find((entry) => entry.id === EXPORT_ID);
if (!exportSurface) {
  exportSurface = { id: EXPORT_ID, tools: [] };
  manifest.bindings.mcp.push(exportSurface);
  changed = true;
}

exportSurface.tools ??= [];
for (const tool of EXPORT_TOOLS) {
  if (!exportSurface.tools.includes(tool)) {
    exportSurface.tools.push(tool);
    changed = true;
  }
}

if (changed) {
  fs.writeFileSync(`${AGENT_PATH}.tmp`, `${JSON.stringify(manifest, null, 2)}\n`);
  fs.renameSync(`${AGENT_PATH}.tmp`, AGENT_PATH);
  console.log(`Configured MCP export surface ${EXPORT_ID}.`);
} else {
  console.log(`MCP export surface ${EXPORT_ID} is already configured.`);
}
