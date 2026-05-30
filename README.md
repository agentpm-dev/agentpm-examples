# agentpm-examples

> **Note:** The code in this repository is **not production-ready**; it’s for demonstration and learning. You can install and test the tools via AgentPM, but don’t rely on them in production.

---

## AgentPM™ Examples Repository

### What is this?
A mono-repo of concrete examples showing how to:
- Build small **tools** (Node + Python),
- Publish them to **AgentPM** with an `agent.json` manifest,
- Load and run them from **agent apps** using several different orchestration styles.

The current examples repo now shows both sides of the agent workflow:

- `agent-packages/*` contains the publishable source manifests for example agents
- the newer `agent-app-*` directories show real apps that install those published agent packages and consume them through the SDKs

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

- **Agent packages**
    - [`agent-packages/research-node`](agent-packages/research-node/)
    - [`agent-packages/ops-python`](agent-packages/ops-python/)
    - [`agent-packages/devwork-python`](agent-packages/devwork-python/)

- **Skill workflow example**
    - [`skill-workflow-slack-post-message`](skill-workflow-slack-post-message/)

### Current agent patterns

The current recommended agent examples in this repo are:

- `agent-app-research-node`
  - Manual OpenAI tool calling loop
  - Consumes the published `@zack/research-console` agent package
  - Best for learning the core mechanics of tool-calling agents
- `agent-app-ops-python`
  - LangChain-managed tools agent
  - Consumes the published `@zack/ops-console` agent package
  - Best for showing a higher-level framework loop over installed AgentPM tools
- `agent-app-devwork-python`
  - LangGraph workflow with explicit approval gating
  - Consumes the published `@zack/devwork-copilot` agent package
  - Best for showing stateful workflows and safe write actions

The older `agent-app-node` and `agent-app-python` directories are still present as earlier examples, but the three apps above are the clearest current patterns.

### Example groups

Some examples in this repo focus on core reusable building blocks:

- `web-page-extract`: fetch and normalize a page into metadata, links, and cleaned content
- `markdown-chunk`: split text into deterministic chunks with heading context
- `csv-query`: filter, sort, group, and aggregate CSV data
- `json-transform`: apply reusable transformations to JSON objects and arrays

Some focus on external system integrations:

- `github-issues`: list, create, comment on, and update GitHub issues
- `slack-post-message`: post or update Slack messages for notifications and agent status updates

And some focus on retrieval and document-heavy workflows:

- `robots-aware-crawl`: bounded multi-page crawling with robots.txt awareness
- `document-convert`: normalize local documents into markdown or text
- `table-extract`: turn HTML or CSV tables into structured rows and columns

### Interoperability surfaces

AgentPM tools in this repo can be used through several different surfaces:

- SDK loading inside agent apps with the Node and Python SDKs
- shell execution with `agentpm run`
- local MCP exposure with `agentpm serve --mcp`
- starter Skill scaffolds with `agentpm export --skill`

Example flow using the published `@zack/slack-post-message` tool:

```bash
agentpm install @zack/slack-post-message
agentpm run @zack/slack-post-message --input '{"action":"post_message","channel":"C123456","text":"hello from AgentPM"}'
agentpm serve --mcp --tool @zack/slack-post-message
agentpm export --skill @zack/slack-post-message
```

That is the main interoperability idea behind this repo:

- package once with AgentPM
- install and run through AgentPM
- expose the same packaged artifact to MCP clients or Skill-based workflows when needed

### Install workflows shown in this repo

This repo currently demonstrates:

- **direct package install for agent apps**
  - `agentpm install @namespace/agent-name@version`
  - the published agent lands in `.agentpm/agents/...`
  - resolved tools land in `.agentpm/tools/...`
  - the app loads the installed agent with the SDK and then loads its resolved tools

- **manifest/package authoring**
  - `agent-packages/*` contains the source manifests used to publish the example agents
  - tool examples continue to show direct manifest authoring and publishing with `agent.json`

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

### Running the core building block tests

```bash
cd tools-node/web-page-extract && npm test
cd tools-python/markdown-chunk && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/csv-query && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/json-transform && python -m unittest discover -s tests -p 'test_*.py'
```

### Running the integration tool tests

```bash
cd tools-node/github-issues && npm test
cd tools-node/slack-post-message && npm test
```

### Running the retrieval and document tests

```bash
cd tools-node/robots-aware-crawl && npm test
cd tools-python/document-convert && python -m unittest discover -s tests -p 'test_*.py'
cd tools-python/table-extract && python -m unittest discover -s tests -p 'test_*.py'
```

### Running the current agent apps

```bash
cd agent-app-research-node && agentpm install @zack/research-console@0.1.1 && pnpm dev
cd agent-app-ops-python && agentpm install @zack/ops-console@0.1.0 && uv run python -m dotenv -f .env.local run -- python -m app.main
cd agent-app-devwork-python && agentpm install @zack/devwork-copilot@0.1.0 && uv run python -m dotenv -f .env.local run -- python -m app.main
```
