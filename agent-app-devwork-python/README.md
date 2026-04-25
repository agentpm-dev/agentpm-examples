# agent-app-devwork-python

Interactive local GitHub maintainer copilot built on the AgentPM Python SDK and an explicit LangGraph workflow.

## What it does

This app loads the published tool specs listed in its local `agent.json`, turns them into callable structured tools, and runs a graph-driven devwork loop.

It is designed to show a different agent style from the other examples:

- `agent-app-research-node` uses a manual OpenAI tool-calling loop
- `agent-app-ops-python` uses a framework-managed tools agent
- `agent-app-devwork-python` uses an explicit graph with state and guarded transitions

The graph is intentionally simple but sturdy:

- assistant planning node
- tool execution node
- approval gate for GitHub write actions
- explicit `/approve` and `/cancel` flow for pending writes

## Pattern

- orchestration style: LangGraph state machine with guarded transitions
- runtime: Python
- best for: showing explicit workflow state, approval gates, and safer write-capable agent behavior

## Tooling model

- tools are installed with `agentpm install` from this directory
- tools are loaded dynamically from `agent.json`
- the app uses the AgentPM Python SDK to invoke installed tools as functions
- LangGraph manages the state machine and approval gate

## Tool set

The default `agent.json` is aimed at GitHub maintainer workflows:

- `@zack/github-issues`
- `@zack/summarize-text`

You can change the tool list in `agent.json` and rerun `agentpm install`.

## Setup

From this app directory:

```bash
uv sync
```

## Install and run

From this app directory:

```bash
agentpm install
cp .env.example .env.local
uv run python -m dotenv -f .env.local run -- python -m app.main
```

## Install AgentPM tools

From this app directory:

```bash
agentpm install
```

That installs the tool set defined in `agent.json` into the app-local `.agentpm/` directory.

## Environment

Create a local env file:

```bash
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL`
- `GITHUB_TOKEN`

## Run

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-devwork-python
uv run python -m dotenv -f .env.local run -- python -m app.main
```

## Run tests

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-devwork-python
uv run python -m unittest discover -s tests -p 'test_*.py'
```

## REPL commands

- `/help`: show commands
- `/tools`: list loaded tools
- `/approve`: execute the currently pending GitHub write action
- `/cancel`: discard the currently pending GitHub write action
- `/reset`: clear conversation history and pending actions
- `/quit`: exit

## Example prompts

- `List the open issues in agentpm-dev/agentpm-examples and tell me which one should be handled first.`
- `Review open issues in agentpm-dev/agentpm-examples and draft a maintainer comment for the most recent one asking whether it is still reproducible.`
- `Look at issue #18 in agentpm-dev/agentpm-examples and propose a concise follow-up comment, but do not post it yet.`
- `Comment on issue #18 that it should be resolved now.`

For write requests, the app should stop and ask for `/approve` before executing the GitHub mutation.

## Notes

- This app is intentionally read/write aware. GitHub write actions are gated behind explicit user approval.
- The graph keeps local conversational state across turns until `/reset`.
- Tool calls and tool outputs are logged so the execution path is easy to inspect.
- If you want to show how AgentPM tools can be used inside a stateful workflow rather than a freeform agent loop, start here.
