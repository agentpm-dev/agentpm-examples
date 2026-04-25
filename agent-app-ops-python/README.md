# agent-app-ops-python

Interactive local ops console built on the AgentPM Python SDK and a LangChain tools agent.

## What it does

This app loads the published tool specs listed in its local `agent.json`, turns them into LangChain structured tools, and runs an interactive ops loop. It is intentionally local-only and not meant to represent what a published AgentPM agent will look like.

The app is designed to make framework-driven orchestration obvious:

- it keeps running and accepts multiple prompts
- LangChain decides which tools to call
- it prints tool start events and arguments
- it prints summarized tool outputs
- it keeps chat history until you reset it

## Tooling model

- tools are installed with `agentpm install` from this directory
- tools are loaded dynamically from `agent.json`
- the app uses the AgentPM Python SDK to invoke installed tools as functions
- LangChain handles the tool-calling loop and final answer generation

## Tool set

The default `agent.json` is aimed at operational workflows:

- `@zack/github-issues`
- `@zack/slack-post-message`
- `@zack/csv-query`
- `@zack/json-transform`

You can change the tool list in `agent.json` and rerun `agentpm install`.

## Setup

From this app directory:

```bash
uv sync
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
- `GITHUB_TOKEN` if you want the agent to read or update GitHub issues
- `SLACK_BOT_TOKEN` if you want the agent to post or update Slack messages

## Run in dev mode

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-ops-python
uv run python -m dotenv -f .env.local run -- python -m app.main
```

## Build

This Python app does not have a separate build step. `uv sync` is the setup step, and `uv run python -m dotenv -f .env.local run -- python -m app.main` runs the app directly.

## Run tests

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-ops-python
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
