# agent-app-research-node

Interactive local research console built on the AgentPM Node SDK.

## What it does

This app loads the published tool specs listed in its local `agent.json`, turns them into callable tool definitions, and runs an interactive research loop. It is intentionally local-only and not meant to represent what a published AgentPM agent will look like.

The app is designed to make tool orchestration obvious:

- it keeps running and accepts multiple prompts
- it shows which tools the model picked
- it prints tool arguments before each call
- it prints a summarized view of each tool result

## Pattern

- orchestration style: manual OpenAI tool-calling loop
- runtime: Node
- best for: learning the core tool-calling mechanics without much framework abstraction

## Tooling model

- tools are installed with `agentpm install` from this directory
- tools are loaded dynamically from `agent.json`
- the app uses the AgentPM Node SDK to invoke installed tools as functions
- the orchestration loop uses the OpenAI API directly for function/tool calling

## Tool set

The default `agent.json` is aimed at research workflows:

- `@zack/web-page-extract`
- `@zack/robots-aware-crawl`
- `@zack/document-convert`
- `@zack/table-extract`
- `@zack/markdown-chunk`
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

## Install and run

From this app directory:

```bash
agentpm install
cp .env.example .env.local
pnpm dev
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

- `Crawl https://docs.github.com up to 3 pages, identify the main themes, and summarize them in bullets.`
- `Extract the main content from https://docs.github.com and translate the summary to Spanish.`
- `Convert a local HTML or JSON file to markdown, then summarize the result.`
- `Extract the first table from a local HTML file and explain what it contains.`
- `Chunk a long markdown document into sections and summarize the most important points.`

## Notes

- This app is intentionally simple and sturdy, not framework-heavy.
- It keeps conversational history across prompts until you run `/reset`.
- Tool results are truncated in the model context and in logs so the terminal stays readable.
- If you want the clearest example of how AgentPM tools map into raw model tool calls, start here.
