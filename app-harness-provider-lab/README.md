# app-harness-provider-lab

Harness Provider Lab is a process-provider lab for AgentPM Harness.

The generated workspace runs directly through `agentpm harness`; no SDK host app is required. Harness launches local process services for:

- ModelRuntime: `runtime/model-provider.mjs`
- EmbeddingProvider: `runtime/openai-embedding-provider.mjs`
- KnowledgeRuntime: `runtime/reference-knowledge-runtime.mjs`
- MemoryRuntime: `runtime/reference-memory-runtime.mjs`
- Approval controller: `runtime/approval-controller.mjs`

The deterministic model intentionally calls each provider path during a normal run so the resulting report and trace prove the wiring.

This checked-in app was generated from the published `harness-provider-lab` workflow template and then kept in this repo as the canonical Harness provider-lab example. To create your own copy, run `agentpm new @zack/harness-provider-lab <target-dir>` instead of copying this directory.

Template source:

- [`template-packages/harness-provider-lab`](../template-packages/harness-provider-lab)

## Package Shape

This template does not install a published Agent package. `agentpm new` creates the root `agent.json` locally in the generated workspace. That local Agent depends on:

- `@zack/react-loop@0.1.0`
- `@zack/agentpm-docs@0.1.1`
- `@zack/devwork-maintainer-guide@0.1.0`
- `@zack/support-customer-state@0.1.0`

The generated workspace then runs `scripts/configure-agent-bindings.mjs` to bind both Knowledge packages and the Memory package into the `reason` phase. They are intentionally not bound into every phase, so later phases can use the prior phase output instead of repeating provider calls.

## What This Workspace Shows

- canonical process ModelRuntime request/response envelopes
- local vector Knowledge retrieval through a hosted EmbeddingProvider
- external KnowledgeRuntime routing for a published vector Knowledge package
- external MemoryRuntime routing for a published Memory Blueprint
- approval-controller routing for the authored `@zack/react-loop` checkpoint
- safe credential handling with `.env.local` and process `env` projection
- reports and traces that identify which provider bridges executed

## Setup

```bash
cp .env.local.example .env.local
pnpm install
pnpm setup:bindings
```

Set `OPENAI_API_KEY` in `.env.local`. The embedding provider loads `.env.local` itself, and `agentpm.harness.json` also declares `OPENAI_API_KEY` in the process env projection. You do not need to export it manually for the documented commands.

Useful optional values:

- `AGENTPM=/path/to/agentpm` to run a locally built CLI in the package scripts
- `OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1` to point at an OpenAI-compatible embedding endpoint
- `PROVIDER_LAB_MODEL_ID`, `PROVIDER_LAB_KNOWLEDGE_RUNTIME_ID`, and `PROVIDER_LAB_MEMORY_RUNTIME_ID` to relabel the reference services

## First Run

Check readiness:

```bash
agentpm harness --json
```

Open the TUI:

```bash
agentpm harness
```

Or run one headless prompt:

```bash
pnpm run harness:headless -- "Use the provider lab to verify every configured provider bridge."
```

The successful run should include:

- one local Knowledge request against `@zack/agentpm-docs`, using the OpenAI embedding process service
- one external KnowledgeRuntime request against `@zack/devwork-maintainer-guide`
- one external MemoryRuntime write against `@zack/support-customer-state/customer_state`
- one auto-approved checkpoint before `act`

## If It Does Not Run

Run preflight first:

```bash
agentpm harness --json
```

If the embedding provider is unavailable, confirm `OPENAI_API_KEY` is set in `.env.local`. If an external runtime is unavailable, run the matching script directly with a small JSONL frame or inspect `.agentpm-state/` for service lifecycle events.

Credentials should stay in `.env.local` or your shell environment. Do not put API keys in `agentpm.harness.json`, `model.options`, package metadata, phase outputs, or Tool/Knowledge/Memory result payloads. Secret-keyed values are redacted in reports, traces, prompts, and stdout, including when trace content is `full`.

## What To Inspect

- `agentpm.harness.json` for the process-provider configuration
- `runtime/model-provider.mjs` for canonical model actions
- `runtime/openai-embedding-provider.mjs` for OpenAI-compatible embedding calls
- `runtime/reference-knowledge-runtime.mjs` for a compact external KnowledgeRuntime
- `runtime/reference-memory-runtime.mjs` for a compact external MemoryRuntime
- `runtime/approval-controller.mjs` for approval-controller routing
- `scripts/configure-agent-bindings.mjs` for idempotent phase bindings
- `.agentpm-state/` after a run for reports and traces

## Common Next Additions

- Replace the reference KnowledgeRuntime with your Pinecone or pgvector retrieval service.
- Replace the reference MemoryRuntime with your PostgreSQL/pgvector or Redis persistence service.
- Swap the deterministic ModelRuntime for your own model service. Keep provider failures explicit; do not silently fall back to another model.
- Add a process Hook service when external provider requests need preflight, policy, or observability decisions.
- Run headless from a larger script with `agentpm harness --headless --input ... --report ...`.
- Change `trace.content` from `redacted` to `full` only for local debugging; full traces include more operational detail, but secret-keyed values are still redacted.

The TUI requires a real interactive terminal. In CI, prefer `agentpm harness --headless`.

## Tests

```bash
pnpm test
```
