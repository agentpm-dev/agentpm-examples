## http-fetch

### What it does
Make HTTP requests (GET/POST/etc.) and return normalized response metadata and content.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "node", "version": "20" }`
- `"entrypoint": { "command": "node", "args": ["dist/index.js"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks

- Use `HTTP_FETCH_DEFAULT_USER_AGENT` env variable to set User-Agent header value for fallback.
- Use `HTTP_FETCH_PROXY_URL` to route requests through a proxy url.

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run

```bash

# install and build

pnpm -C tools-node/http-fetch build


# set env and run

echo '{"url":"https://agentpackagemanager.com"}' | node tools-node/http-fetch/dist/index.js
```