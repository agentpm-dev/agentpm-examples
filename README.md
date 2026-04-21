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
    - [`tools-node/wikipedia-scrape`](tools-node/wikipedia-scrape/)
    - [`tools-node/web-page-extract`](tools-node/web-page-extract/)
    - [`tools-node/github-issues`](tools-node/github-issues/)
    - [`tools-node/robots-aware-crawl`](tools-node/robots-aware-crawl/)
    - [`tools-node/slack-post-message`](tools-node/slack-post-message/)
    - [`tools-python/document-convert`](tools-python/document-convert/)
    - [`tools-python/summarize-text`](tools-python/summarize-text/)
    - [`tools-python/markdown-chunk`](tools-python/markdown-chunk/)
    - [`tools-node/translate-text`](tools-node/translate-text/)
    - [`tools-python/sentiment-analysis`](tools-python/sentiment-analysis/)
    - [`tools-python/csv-query`](tools-python/csv-query/)
    - [`tools-python/json-transform`](tools-python/json-transform/)
    - [`tools-python/table-extract`](tools-python/table-extract/)
    - [`tools-node/resize-image`](tools-node/resize-image)
- **Agents**
    - [`agent-app-python`](agent-app-python/)
    - [`agent-app-node`](agent-app-node/)

### Phase 1: Seeding

The first Phase 1 additions are meant to prove there is value in installing shared agent primitives rather than rebuilding them:

- `web-page-extract`: fetch and normalize a page into metadata, links, and cleaned content
- `markdown-chunk`: split text into deterministic chunks with heading context
- `csv-query`: filter, sort, group, and aggregate CSV data
- `json-transform`: apply reusable transformations to JSON objects and arrays

### Milestone 2: Integrations

The next additions prove AgentPM can package tools for external systems people already use:

- `github-issues`: list, create, comment on, and update GitHub issues
- `slack-post-message`: post or update Slack messages for notifications and agent status updates

### Milestone 3: Retrieval and Documents

The final three tools deepen the knowledge and research story:

- `robots-aware-crawl`: bounded multi-page crawling with robots.txt awareness
- `document-convert`: normalize local documents into markdown or text
- `table-extract`: turn HTML or CSV tables into structured rows and columns

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

### Running the Phase 1 tests

```bash
cd tools-node/web-page-extract && npm test
cd tools-python/markdown-chunk && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/csv-query && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/json-transform && python -m unittest discover -s tests -p 'test_*.py'
```

### Running the Milestone 2 tests

```bash
cd tools-node/github-issues && npm test
cd tools-node/slack-post-message && npm test
```

### Running the Milestone 3 tests

```bash
cd tools-node/robots-aware-crawl && npm test
cd tools-python/document-convert && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/table-extract && python -m unittest discover -s tests -p 'test_*.py'
```
