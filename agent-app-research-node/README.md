# agent-app-research-node

Interactive local research assistant built on the AgentPM Node SDK.

## What it does

This app was generated from the published `research-assistant-node` workflow template and then checked into this repo as the canonical Node SDK research example.

It loads the tools declared in the generated `agent.json`, then runs an interactive research workflow against real installed AgentPM packages.

Published template package:

- `@zack/research-assistant-node@0.1.0`

Template source:

- [`template-packages/research-assistant-node`](https://github.com/agentpm-dev/agentpm-examples/tree/main/template-packages/research-assistant-node)

## Pattern

This example shows a real app that:

- is generated with `agentpm new`
- installs tool dependencies through the generated `agent.json`
- loads those installed tools with `load(...)`
- runs an interactive research workflow against real installed packages

- orchestration style: manual OpenAI tool-calling loop
- runtime: Node
- best for: learning the core tool-calling mechanics with a generated local app rather than a published agent package

It is a good fit if you want to:

- fetch and extract webpage content
- crawl a small public source set
- convert local documents into markdown or text
- summarize and translate results

## Setup

From the repo root:

```bash
pnpm install --filter agentpm-examples-agent-app-research-node
```

Or from this app directory:

```bash
pnpm install
```

## Environment

Install Node dependencies:

Create a local env file:

```bash
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL` if you do not want the default `gpt-4o-mini`

## Run in dev mode

```bash
pnpm dev
```

## Build and run

```bash
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

- This checked-in example was originally scaffolded with `agentpm new`.
- `agentpm new` already installed the declared tool dependencies and wrote `agent.lock`.
- If you later edit `agent.json`, rerun `agentpm install` to regenerate `agent.lock`.
- This app keeps conversational history across prompts until you run `/reset`.
