# agent-app-ops-python

Interactive local ops console built on the AgentPM Python SDK and a LangChain tools agent.

## What it does

This app installs the published `ops-console` agent package, loads it with the AgentPM Python SDK, and uses the tools resolved for that agent to run an interactive operations workflow.

Published agent package:

- `@zack/ops-console@0.1.0`

Package source:

- [`agent-packages/ops-python`](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/ops-python)

## Pattern

This example shows a real app that:

- installs a published agent package
- loads that agent with `load_agent(...)`
- reads the resolved tool refs from the agent
- loads those tools with `load(...)`
- runs an interactive operations workflow against real installed packages

- orchestration style: LangChain-managed tools agent
- runtime: Python
- best for: showing a framework-managed agent loop over operational tools like GitHub, Slack, CSV, and JSON transforms

## Expected agent install

From this app directory, install the published agent package:

```bash
agentpm install @zack/ops-console@0.1.0
```

That should install:

- the agent artifact under `.agentpm/agents/...`
- the resolved tool artifacts under `.agentpm/tools/...`

## Setup

From this app directory:

```bash
uv sync
```

## Environment

Create a local env file:

```bash
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL`
- `GITHUB_TOKEN` if you want the agent to read or update GitHub issues
- `SLACK_BOT_TOKEN` if you want the agent to post or update Slack messages

## Run in dev mode

```bash
cd agent-app-ops-python
uv run python -m dotenv -f .env.local run -- python -m app.main
```

## Build

This Python app does not have a separate build step. `uv sync` is the setup step, and `uv run python -m dotenv -f .env.local run -- python -m app.main` runs the app directly.

## Run tests

```bash
cd agent-app-ops-python
uv run python -m unittest discover -s tests -p 'test_*.py'
```

## REPL commands

- `/help`: show commands
- `/tools`: list loaded tools
- `/reset`: clear conversation history
- `/quit`: exit

## Example prompts

- `List the open issues in agentpm-dev/agentpm-examples and summarize the main themes.`
- `Look at open issues in agentpm-dev/agentpm-examples, group them by label if possible, and draft a Slack update but do not send it yet.`
- `Query ./fixtures/incidents.csv for rows with severity above 2, transform the result into a compact status payload, and show me the JSON.`
- `Post this exact message to Slack channel C1234567890: "Daily triage complete. 4 issues need follow-up."`

## Notes

- This app intentionally uses a framework-managed tool loop so it contrasts with the manual OpenAI tool-calls flow in `agent-app-research-node`.
- The prompt tells the model not to write to Slack or GitHub unless the user clearly asked for it.
- Tool results are truncated in logs so the terminal stays readable.
- For file-based prompts, absolute paths are more reliable than relative paths because tools run as subprocesses.
