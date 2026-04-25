# agentpm-examples

> **Note:** The code in this repository is **not production-ready**; it’s for demonstration and learning. You can install and test the tools via AgentPM, but don’t rely on them in production.

---

## AgentPM Examples Repository

### What is this?
A mono-repo of concrete examples showing how to:
- Build small **tools** (Node + Python),
- Publish them to **AgentPM** with an `agent.json` manifest,
- Load and run them from **agent apps** using several different orchestration styles.

Each tool is intentionally simple to highlight integration, not performance.

### Contents
- **Tools**
    - [`tools-node/web-page-extract`](tools-node/web-page-extract/)
    - [`tools-node/wikipedia-scrape`](tools-node/wikipedia-scrape/)
    - [`tools-node/github-issues`](tools-node/github-issues/)
    - [`tools-node/robots-aware-crawl`](tools-node/robots-aware-crawl/)
    - [`tools-node/slack-post-message`](tools-node/slack-post-message/)
    - [`tools-node/translate-text`](tools-node/translate-text/)
    - [`tools-node/resize-image`](tools-node/resize-image)
    - [`tools-python/document-convert`](tools-python/document-convert/)
    - [`tools-python/summarize-text`](tools-python/summarize-text/)
    - [`tools-python/markdown-chunk`](tools-python/markdown-chunk/)
    - [`tools-python/sentiment-analysis`](tools-python/sentiment-analysis/)
    - [`tools-python/csv-query`](tools-python/csv-query/)
    - [`tools-python/json-transform`](tools-python/json-transform/)
    - [`tools-python/table-extract`](tools-python/table-extract/)
    
- **Agents**
    - [`agent-app-research-node`](agent-app-research-node/)
    - [`agent-app-ops-python`](agent-app-ops-python/)
    - [`agent-app-devwork-python`](agent-app-devwork-python/)
    - [`agent-app-python`](agent-app-python/)
    - [`agent-app-node`](agent-app-node/)

### Current agent patterns

The current recommended agent examples in this repo are:

- `agent-app-research-node`
  - Manual OpenAI tool calling loop
  - Best for learning the core mechanics of tool-calling agents
- `agent-app-ops-python`
  - LangChain-managed tools agent
  - Best for showing a higher-level framework loop over installed AgentPM tools
- `agent-app-devwork-python`
  - LangGraph workflow with explicit approval gating
  - Best for showing stateful workflows and safe write actions

The older `agent-app-node` and `agent-app-python` directories are still present as earlier examples, but the three apps above are the clearest current patterns.

### Phase 1: Seeding

The first Phase 1 additions are meant to prove there is value in installing shared agent primitives rather than rebuilding them:

- `web-page-extract`: fetch and normalize a page into metadata, links, and cleaned content
- `markdown-chunk`: split text into deterministic chunks with heading context
- `csv-query`: filter, sort, group, and aggregate CSV data
- `json-transform`: apply reusable transformations to JSON objects and arrays

### Phase 2: Integrations

The next additions prove AgentPM can package tools for external systems people already use:

- `github-issues`: list, create, comment on, and update GitHub issues
- `slack-post-message`: post or update Slack messages for notifications and agent status updates

### Phase 3: Retrieval and Documents

The final three tools deepen the knowledge and research story:

- `robots-aware-crawl`: bounded multi-page crawling with robots.txt awareness
- `document-convert`: normalize local documents into markdown or text
- `table-extract`: turn HTML or CSV tables into structured rows and columns

### Quick workspace setup
```bash
# from repo root
pnpm -r install                    # installs Node deps for node tools & node apps
uv sync --directory agent-app-python
uv sync --directory agent-app-ops-python
uv sync --directory agent-app-devwork-python
uv sync --directory tools-python/summarize-text
uv sync --directory tools-python/sentiment-analysis
```

> Env files: for SDKs needing keys, use `.env.local` in the corresponding package (see each README).

---

### Portability & dependencies (Python vendoring, JS bundling)

#### Python (vendoring)

Python example tools prefer vendored pure-Python dependencies so the published artifact stays self-contained and does not depend on the target environment having already installed package dependencies.

The point is portability: AgentPM installs a tool artifact and then runs it, so bundling the Python dependency tree into the tool makes behavior more predictable across machines.

#### JavaScript/Node (bundling)

Node example tools prefer bundling so the runtime artifact is a small, explicit `dist/` payload rather than a source tree plus a larger dependency install story.

The point here is the same: publish the thing you actually want executed. That keeps installation simpler and makes the packaged tool easier to reason about.

### Running the Phase 1 tests

```bash
cd tools-node/web-page-extract && npm test
cd tools-python/markdown-chunk && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/csv-query && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/json-transform && python -m unittest discover -s tests -p 'test_*.py'
```

### Running the Phase 2 tests

```bash
cd tools-node/github-issues && npm test
cd tools-node/slack-post-message && npm test
```

### Running the Phase 3 tests

```bash
cd tools-node/robots-aware-crawl && npm test
cd tools-python/document-convert && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/table-extract && python -m unittest discover -s tests -p 'test_*.py'
```

### Running the current agent apps

```bash
cd agent-app-research-node && agentpm install && pnpm dev
cd agent-app-ops-python && agentpm install && uv run python -m dotenv -f .env.local run -- python -m app.main
cd agent-app-devwork-python && agentpm install && uv run python -m dotenv -f .env.local run -- python -m app.main
```
