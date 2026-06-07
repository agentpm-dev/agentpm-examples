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
- `template-packages/*` contains the publishable source manifests for official workflow templates
- the newer `agent-app-*` directories show real apps that either install published agent packages or are generated from published workflow templates and then consumed through the SDKs

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
    - [`agent-app-support-assistant-workspace`](agent-app-support-assistant-workspace/)
    - [`agent-app-devwork-python`](agent-app-devwork-python/)
    - [`app-cli-automation-worker`](app-cli-automation-worker/)
    - [`app-mcp-tool-server`](app-mcp-tool-server/)
    - [`agent-app-python`](agent-app-python/)
    - [`agent-app-node`](agent-app-node/)

- **Agent packages**
    - [`agent-packages/research-node`](agent-packages/research-node/)
    - [`agent-packages/ops-python`](agent-packages/ops-python/)
    - [`agent-packages/devwork-python`](agent-packages/devwork-python/)

- **Workflow templates**
    - [`template-packages/research-assistant-node`](template-packages/research-assistant-node/)
    - [`template-packages/triage-worker-python`](template-packages/triage-worker-python/)
    - [`template-packages/cli-automation-worker`](template-packages/cli-automation-worker/)
    - [`template-packages/mcp-tool-server`](template-packages/mcp-tool-server/)
    - [`template-packages/support-assistant-workspace`](template-packages/support-assistant-workspace/)

- **Skill workflow example**
    - [`skill-workflow-slack-post-message`](skill-workflow-slack-post-message/)

### Current agent patterns

The current recommended agent examples in this repo are:

- `agent-app-research-node`
  - Manual OpenAI tool calling loop
  - Generated from the published `@zack/research-assistant-node` workflow template
  - Best for learning the core mechanics of tool-calling agents in a generated local app
- `agent-app-ops-python`
  - LangChain-managed tools agent
  - Generated from the published `@zack/triage-worker-python` workflow template
  - Best for showing a Python template-generated app that mixes a published agent root with one direct local-manifest tool
- `agent-app-support-assistant-workspace`
  - Multi-manifest Python workspace
  - Generated from the published `@zack/support-assistant-workspace` workflow template
  - Best for showing the real AgentPM workspace shape with one published agent root plus local generated `agents/*.agent.json`
- `agent-app-devwork-python`
  - LangGraph workflow with explicit approval gating
  - Consumes the published `@zack/devwork-copilot` agent package
  - Best for showing stateful workflows and safe write actions
- `app-cli-automation-worker`
  - Shell-first `agentpm run` workflow
  - Generated from the published `@zack/cli-automation-worker` workflow template
  - Best for showing file-based CLI automation without writing SDK code
- `app-mcp-tool-server`
  - Local HTTP MCP server
  - Generated from the published `@zack/mcp-tool-server` workflow template
  - Best for showing how AgentPM can expose a curated pinned tool set over MCP without extra app code

The older `agent-app-node` and `agent-app-python` directories are still present as earlier examples, but the six apps above are the clearest current patterns.

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

- **template-generated app bootstrap**
  - `agentpm new @namespace/template-name target-dir`
  - the generated app receives a root `agent.json`, `agent.lock`, `agentpm.workspace.json`, and `.agentpm/template.json`
  - the app then loads the installed tools declared in the generated local manifest

- **manifest/package authoring**
  - `agent-packages/*` contains the source manifests used to publish the example agents
  - `template-packages/*` contains the source manifests used to publish official workflow templates
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
cd agent-app-research-node && pnpm dev
cd agent-app-ops-python && agentpm install && uv sync && uv run python -m dotenv -f .env.local run -- python -m app.main
cd agent-app-support-assistant-workspace && cp .env.example .env.local && agentpm install && uv sync && uv run python app/main.py
cd agent-app-devwork-python && agentpm install @zack/devwork-copilot@0.1.0 && uv run python -m dotenv -f .env.local run -- python -m app.main
cd app-cli-automation-worker && cp .env.example .env.local && agentpm install && bash scripts/run-daily-brief.sh
cd app-mcp-tool-server && cp .env.example .env.local && agentpm install && set -a && source .env.local && set +a && agentpm serve --mcp
```
