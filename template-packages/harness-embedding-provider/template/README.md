# {{ project_name }}

{{ workspace_label }} is a Node SDK host example for AgentPM Harness embeddings.

The app can run two ways:

- standalone through `agentpm harness`, including the TUI
- SDK-hosted through `pnpm dev`, with the Node app driving `agentpm harness --machine`

Both paths use the published `@zack/react-loop` Loop and the refreshed published `@zack/agentpm-docs@0.1.1` Knowledge package as the retrieval target.

## Package Shape

This template does not install a published Agent package. `agentpm new` creates the root `agent.json` locally in the generated workspace. That local Agent depends on:

- `@zack/react-loop@0.1.0`
- `@zack/agentpm-docs@0.1.1`

The binding in `agentpm.harness.json` is a standalone runtime-service binding:

- `local-openai-embeddings` runs as `runtime/openai-embedding-provider.mjs`
- `knowledge.embedding_matches` maps the docs package embedding spec to that hosted provider

`agentpm new` generates the root `agent.json` from the published package dependencies. This app also includes `scripts/configure-agent-bindings.mjs`, which adds the phase-level Knowledge binding needed by Harness. It binds docs Knowledge only into `reason` so later `act` and `reflect` phases can use the prior phase output instead of repeatedly retrieving. `pnpm dev` runs it automatically before starting Harness.

`agentpm.sdk.harness.json` keeps the SDK-hosted variant:

- `local-openai-embeddings` is registered by `src/main.ts`
- the approval controller is registered by `src/main.ts` so the published `@zack/react-loop` checkpoint can continue without opening the TUI

That is the intended quick-start shape: local Agent, published Loop and Knowledge package, and either process-hosted or app-hosted embeddings.

## What This Workspace Shows

- direct `agentpm harness` / TUI execution with a process EmbeddingProvider
- `HarnessClient` driving `agentpm harness --machine` for SDK-hosted execution
- a reusable EmbeddingProvider named `local-openai-embeddings`
- OpenAI `text-embedding-3-small` query vectors for the installed docs Knowledge package
- provider/model/dimensions/normalized matching between `agentpm.harness.json` and the Knowledge package
- a minimal approval callback for the authored `@zack/react-loop` checkpoint
- event streaming, report access, and deterministic shutdown
- Ctrl+C cancellation through `cancelRun()`

## Setup

```bash
cp .env.local.example .env.local
pnpm install
pnpm setup:bindings
```

Set `OPENAI_API_KEY` in `.env.local`. The app loads `.env.local` automatically with `dotenv`; you do not need to export those variables manually for `pnpm dev`.

Useful optional values:

- `AGENTPM=/path/to/agentpm` to run a locally built CLI
- `SDK_HOST_USER={{ default_user_scope }}` to change the user scope sent by the SDK host
- `OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1` to point at an OpenAI-compatible embedding endpoint

## First Run

Configure the local Agent bindings once:

```bash
pnpm setup:bindings
```

Start with standalone preflight:

```bash
agentpm harness --json
```

Then open the TUI:

```bash
agentpm harness
```

Or run through the Node SDK host:

```bash
pnpm dev -- --preflight-only
```

Then run a Knowledge-backed prompt:

```bash
pnpm dev -- "Use the AgentPM docs Knowledge package to explain how Harness SDK-hosted providers work."
```

You should see Knowledge and embedding events in the terminal output and a report/trace path at the end.

## If It Does Not Run

Run preflight first:

```bash
pnpm dev -- --preflight-only
```

If the SDK app cannot find the CLI, set `AGENTPM` in `.env.local`. If the full run fails before retrieval, confirm `OPENAI_API_KEY` is set and that `agentpm.harness.json` still uses the same embedding metadata as the docs package: provider `openai`, model `text-embedding-3-small`, dimensions `1536`, normalized `true`.

Credentials should stay in `.env.local` or your shell environment. Do not put API keys in `agentpm.harness.json`, `model.options`, package metadata, phase outputs, or Tool/Knowledge result payloads. Secret-keyed values are redacted in reports, traces, prompts, and stdout, including when trace content is `full`.

## What To Inspect

- `src/main.ts` for the hosted embedding provider, OpenAI request, event printing, and cancellation handler
- `runtime/openai-embedding-provider.mjs` for the standalone process EmbeddingProvider used by the TUI
- `scripts/configure-agent-bindings.mjs` for the idempotent local Agent binding setup
- `agentpm.harness.json` for standalone TUI/headless process-provider binding
- `agentpm.sdk.harness.json` for SDK-hosted embedding and approval binding
- `agent.lock` for the installed `@zack/react-loop` and `@zack/agentpm-docs` dependencies
- `.agentpm-state/` after a run for reports and traces

## Common Next Additions

- Swap OpenAI embeddings for your own service by replacing `embedWithOpenAI()` and updating both the host capabilities and `knowledge.embedding_matches`.
- Add a hosted KnowledgeRuntime when your source data lives outside an AgentPM vector package.
- Add a Memory semantic search path by wiring `memory.local.semantic` to the same embedding provider.
- Change the model in `agentpm.harness.json`; keep credentials in environment variables.
- Run headless from a larger script by calling `agentpm harness --headless` directly, or keep the SDK host pattern shown in `src/main.ts` when the embedding provider must live inside your app process.
- Change `trace.content` from `redacted` to `full` only for local debugging; full traces include more operational detail, but secret-keyed values are still redacted.

The TUI requires a real interactive terminal. In CI, prefer this SDK machine app or `agentpm harness --headless`.

## Tests

```bash
pnpm test
```
