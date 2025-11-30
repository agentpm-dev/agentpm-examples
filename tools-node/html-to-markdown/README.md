## html-to-markdown

### What it does
Convert raw HTML into Markdown and plain text, with optional main-content extraction.


### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "node", "version": "20" }`
- `"entrypoint": { "command": "node", "args": ["dist/index.js"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks
- Use `HTML2MD_DEFAULT_BASE_URL` to define default base URL used to resolve relative links when base_url is not provided in inputs.
- `node_modules` is packaged with this tool to handle jsdom issues when not externalized with esbuild

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.


### Setup & run

```bash

# install and build

pnpm -C tools-node/html-to-markdown build

# set env and run

echo '{"url":"https://agentpackagemanager.com"}' \
  | node tools-node/http-fetch/dist/index.js \
  | jq -r 'select(.ok == true) | {html: .body_text, main_content_only: true, base_url: "https://agentpackagemanager.com"} | @json' \
  | node tools-node/html-to-markdown/dist/index.js \
  | jq -r '.markdown'
  
```