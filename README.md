# agentpm-examples

> **Note:** The code in this repository is **not production-ready**; it’s for demonstration and learning. You can install and test the tools via AgentPM, but don’t rely on them in production.

---

## AgentPM Examples Repository

### What is this?
A mono-repo of concrete examples showing how to:
- Build small **tools** (Node + Python),
- Publish them to **AgentPM** with an `agent.json` manifest,
- Load and run them from **agent apps** using LangChain (Python and Node).

Each tool is intentionally simple to highlight integration, not performance.

### Contents
- **Tools**
    - [`tools-node/wikipedia-scrape`](#2-wikipedia-scrape--readme)
    - [`tools-python/summarize-text`](#3-summarize-text--readme)
    - [`tools-node/translate-text`](#4-translate-text--readme)
    - [`tools-python/sentiment-analysis`](#5-sentiment-analysis--readme)
    - [`tools-node/resize-image`](#6-resize-image--readme)
- **Agents**
    - [`agent-app-python`](#7-python-agent--readme)
    - [`agent-app-node`](#8-node-agent--readme)

### Quick workspace setup
```bash
# from repo root
pnpm -r install                    # installs Node deps for node tools & node agent
uv sync --directory agent-app-python
uv sync --directory tools-python/summarize-text
uv sync --directory tools-python/sentiment-analysis
```

> Env files: for SDKs needing keys, use `.env.local` in the corresponding package (see each README).

---

### Portability & dependencies (Python vendoring, JS bundling)

#### Python (vendoring)

Prefer **pure-Python** deps and vendor them into the tool (e.g., `tool_pkg/_vendor/`), then prepend to `sys.path` in your entrypoint:

```pycon
import sys, pathlib
here = pathlib.Path(__file__).resolve().parent
v = here / "_vendor"
if v.exists(): sys.path.insert(0, str(v))
```

#### JavaScript/Node (bundling)

Use a bundler (e.g., **tsup/esbuild**) to produce a single dist file (CJS or ESM). Your `agent.json` should point the entrypoint at dist/….

```json
"files": ["dist/"],
"entrypoint": { "command": "node", "args": ["dist/index.js"] }
```

pnpm -r install

pnpm -C tools-node/wikipedia-scrape build

pnpm -C tools-node/wikipedia-scrape add -D @types/node@^22 typescript@^5

echo '{"url":"https://en.wikipedia.org/wiki/Alan_Turing"}' | node tools-node/wikipedia-scrape/dist/index.js

pnpm -C tools-node/translate-text add -D dotenv-cli

pnpm -C tools-node/translate-text build

NODE_OPTIONS=--no-deprecation \
pnpm --dir tools-node/translate-text exec dotenv -e .env.local -- \
node dist/index.js <<'JSON'
{"text":"Hello world","target_language":"Spanish"}
JSON


uv sync --directory tools-python/summarize-text

uv add --directory tools-python/summarize-text python-dotenv
uv add --directory tools-python/summarize-text "python-dotenv[cli]"

uv run --directory tools-python/summarize-text \
python -m dotenv -f .env.local run -- \
python -m summarize_text <<'JSON'
{"text":"Alan Turing was a computer scientist","max_words":60}
JSON

uv pip install --target tools-python/summarize-text/summarize_text/_vendor "openai>=1.51.0"


uv sync --directory tools-python/sentiment-analysis

uv pip install --target tools-python/sentiment-analysis/sentiment_analysis/_vendor "vaderSentiment>=3.3.2"

uv run --directory tools-python/sentiment-analysis \
python -m sentiment_analysis <<'JSON'
{"text":"Alan Turing is one of history's most influential computer scientists"}
JSON

pnpm -C tools-node/resize-image build 

Note - cjs instead of js for jimp

echo '{"url":"https://upload.wikimedia.org/wikipedia/commons/a/a1/Alan_Turing_Aged_16.jpg","width":320,"height":180}' | node tools-node/resize-image/dist/index.cjs


uv sync --directory agent-app-python


agentpm publish --dry-run
• Reading credentials…
✓ Reading credentials (0ms)
• Validating manifest…
✓ Validating manifest (196ms) — schema + semantics
• Packaging files…
✓ Packaging files (104ms) — 693129 bytes, sha256: 1e538aaed235
Dry-run: package created at target/agentpm/wikipedia-scrape-0.1.0.tar.gz

agentpm publish
• Reading credentials…
✓ Reading credentials (0ms)
• Validating manifest…
✓ Validating manifest (124ms) — schema + semantics
• Packaging files…
✓ Packaging files (96ms) — 693129 bytes, sha256: 1e538aaed235
• Uploading artifact…
✓ Uploading artifact (3.5s) — done
✓ Published wikipedia-scrape@0.1.0
id:   2
url:  https://www.agentpackagemanager.com/tools/13ad27db-a5ed-4472-a996-3f3f0e1e270b/v0.1.0/overview


uv run --directory agent-app-python \
python -m dotenv -f .env.local run -- \
python -m app.main



pnpm -w add langchain@^0.2 @langchain/core@^0.2 @langchain/openai@^0.3 -F agent-app-node

pnpm --dir agent-app-node add -D dotenv-cli

pnpm --dir agent-app-node exec dotenv -e .env.local -- pnpm --dir agent-app-node dev


