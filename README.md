# agentpm-examples

> **Note:** The code in this repository is **not production-ready**; it’s for demonstration and learning. You can install and test the tools via AgentPM, but don’t rely on them in production.

---

## AgentPM™ Examples Repository

### What is this?
A mono-repo of concrete examples showing how to:
- Build small **tools** (Node + Python),
- Publish them to **AgentPM** with an `agent.json` manifest,
- Load and run them from **agent apps** using LangChain (Python and Node).

Each tool is intentionally simple to highlight integration, not performance.

### Contents
- **Tools**
    - [`tools-node/wikipedia-scrape`](tools-node/wikipedia-scrape/)
    - [`tools-python/summarize-text`](tools-python/summarize-text/)
    - [`tools-node/translate-text`](tools-node/translate-text/)
    - [`tools-python/sentiment-analysis`](tools-python/sentiment-analysis/)
    - [`tools-node/resize-image`](tools-node/resize-image)
- **Agents**
    - [`agent-app-python`](agent-app-python/)
    - [`agent-app-node`](agent-app-node/)

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


