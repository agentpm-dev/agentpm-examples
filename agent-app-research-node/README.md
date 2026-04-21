# agent-app-research-node

Interactive local research console built on the AgentPM Node SDK.

## What it does

This app loads the published tool specs listed in its local `agent.json`, turns them into callable tool definitions, and runs an interactive research loop. It is intentionally local-only and not meant to represent what a published AgentPM agent will look like.

The app is designed to make tool orchestration obvious:

- it keeps running and accepts multiple prompts
- it shows which tools the model picked
- it prints tool arguments before each call
- it prints a summarized view of each tool result

## Tooling model

- tools are installed with `agentpm install` from this directory
- tools are loaded dynamically from `agent.json`
- the app uses the AgentPM Node SDK to invoke installed tools as functions
- the orchestration loop uses the OpenAI API directly for function/tool calling

## Tool set

The default `agent.json` is aimed at research workflows:

- `@zack/wikipedia-scrape`
- `@zack/http-fetch`
- `@zack/html-to-markdown`
- `@zack/pdf-to-text`
- `@zack/summarize-text`
- `@zack/translate-text`

You can change the tool list in `agent.json` and rerun `agentpm install`.

## Setup

From the repo root:

```bash
pnpm install --filter agentpm-examples-agent-app-research-node
```

Or from this app directory:

```bash
pnpm install
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
- optionally `OPENAI_MODEL` if you do not want the default `gpt-4o-mini`

## Run in dev mode

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-research-node
pnpm dev
```

## Build and run

```bash
cd /Users/zackhine/projects/agentpm-project/agentpm-examples/agent-app-research-node
pnpm build
pnpm start
```

## REPL commands

- `/help`: show commands
- `/tools`: list loaded tools
- `/reset`: clear conversation history
- `/quit`: exit

## Example prompts

- `Research the Alan Turing Wikipedia article, summarize the key contributions, and translate the summary to Spanish.`
- `Fetch https://docs.github.com and summarize the landing page.`
- `Given a PDF URL, extract the text and summarize it in bullets.`

## Notes

- This app is intentionally simple and sturdy, not framework-heavy.
- It keeps conversational history across prompts until you run `/reset`.
- Tool results are truncated in the model context and in logs so the terminal stays readable.
