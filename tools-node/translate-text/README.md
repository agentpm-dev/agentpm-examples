## translate-text

### What it does
Translates text to a target language using OpenAI.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "node", "version": "20" }`
- `"entrypoint": { "command": "node", "args": ["dist/index.js"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks
- Requires `OPENAI_API_KEY`.

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run
```bash
# install and build
pnpm -C tools-node/translate-text build

# set env and run
NODE_OPTIONS=--no-deprecation \
pnpm --dir tools-node/translate-text exec dotenv -e .env.local -- \
node dist/index.js <<'JSON'
{"text":"Hello world","target_language":"Spanish"}
JSON
```