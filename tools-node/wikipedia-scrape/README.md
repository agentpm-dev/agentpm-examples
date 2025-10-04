## wikipedia-scrape

### What it does
Fetches a Wikipedia article URL and returns:
- `title` (string)
- `text` (full extracted text)
- `images` (array/list of image URLs or a serialized string, per the manifest)

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "node", "version": "20" }`
- `"entrypoint": { "command": "node", "args": ["dist/index.js"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks
- Uses `undici` with a custom `User-Agent`.

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.


### Run in isolation
```bash
pnpm -C tools-node/wikipedia-scrape build

echo '{"url":"https://en.wikipedia.org/wiki/Alan_Turing"}' | node tools-node/wikipedia-scrape/dist/index.js
```