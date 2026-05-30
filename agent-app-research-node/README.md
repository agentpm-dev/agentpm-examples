# agent-app-research-node

Interactive local research console built on the AgentPM Node SDK.

## What it does

This app installs the published `research-console` agent package, loads it with the AgentPM Node SDK, and uses the tools resolved for that agent to run an interactive research workflow.

Published agent package:

- `@zack/research-console@0.1.1`

Package source:

- [`agent-packages/research-node`](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/research-node)

## Pattern

This example shows a real app that:

- installs a published agent package
- loads that agent with `loadAgent(...)`
- reads the resolved tool refs from the agent
- loads those tools with `load(...)`
- runs an interactive research workflow against real installed packages

- orchestration style: manual OpenAI tool-calling loop
- runtime: Node
- best for: learning the core tool-calling mechanics without much framework abstraction

## Expected agent install

From this app directory, install the published agent package:

```bash
agentpm install @zack/research-console@0.1.1
```

That should install:

- the agent artifact under `.agentpm/agents/...`
- the resolved tool artifacts under `.agentpm/tools/...`

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

Create a local env file:

```bash
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL` if you do not want the default `gpt-4o-mini`

## Run in dev mode

```bash
cd agent-app-research-node
pnpm dev
```

## Build and run

```bash
cd agent-app-research-node
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
