## resize-image

### What it does
Downloads an image (e.g., from Wikipedia), resizes it, and returns a **base64 JPEG**.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "node", "version": "20" }`
- `"entrypoint": { "command": "node", "args": ["dist/index.cjs"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks
- Uses `undici` + `Jimp`. Keep-alive disabled; deterministic exit after writing JSON.
- Handles large outputs by **chunking** JSON to stdout to avoid pipe backpressure.

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run
```bash
# install and build
pnpm -C tools-node/resize-image build 

# run
echo '{"url":"https://upload.wikimedia.org/wikipedia/commons/a/a1/Alan_Turing_Aged_16.jpg","width":320,"height":180}' | node tools-node/resize-image/dist/index.cjs
```