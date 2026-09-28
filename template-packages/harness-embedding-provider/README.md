# harness-embedding-provider

`harness-embedding-provider` is a publishable AgentPM workflow template for users who want to run Harness with a local SDK-hosted embedding provider.

Generated apps use a local root `agent.json`. The local Agent depends on the published `@zack/react-loop@0.1.0` Loop and the refreshed published `@zack/agentpm-docs@0.1.1` Knowledge package, while `agentpm.harness.json` maps that Knowledge package's vector embedding spec to the Node host provider in `src/main.ts`.

## What It Demonstrates

- A Node SDK Harness host with one focused EmbeddingProvider implementation
- OpenAI `text-embedding-3-small` query embedding for a published AgentPM Knowledge package
- `knowledge.embedding_matches` alignment across provider, model, dimensions, and normalized vector metadata
- A normal Harness run where Knowledge retrieval can feed a multi-phase Loop
- Safe credential handling through `.env.local`, not `agentpm.harness.json`

## Generate Locally

```bash
agentpm new ./template-packages/harness-embedding-provider/agent.json app-harness-embedding-provider
cd app-harness-embedding-provider
cp .env.local.example .env.local
pnpm install
pnpm dev -- --preflight-only
```

Set `OPENAI_API_KEY` in `.env.local` before the full run.

## Publish Checks

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Template package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/template-packages/harness-embedding-provider).
