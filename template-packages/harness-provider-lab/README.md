# harness-provider-lab

`harness-provider-lab` is a publishable AgentPM workflow template for users who want to see every main Harness provider bridge running from local process services.

Generated apps use a local root `agent.json` that depends on published packages:

- `@zack/react-loop@0.1.0`
- `@zack/agentpm-docs@0.1.1`
- `@zack/devwork-maintainer-guide@0.1.0`
- `@zack/support-customer-state@0.1.0`

The generated `agentpm.harness.json` wires process-hosted ModelRuntime, EmbeddingProvider, external KnowledgeRuntime, external MemoryRuntime, and approval controller services.

## What It Demonstrates

- a deterministic process ModelRuntime that proposes canonical Harness actions
- a process EmbeddingProvider for the local `@zack/agentpm-docs` vector Knowledge package
- a process KnowledgeRuntime for a published vector Knowledge package
- a process MemoryRuntime for a published Memory Blueprint
- environment-based credential projection with no literal credentials in Harness config or package metadata
- the difference between the quick-start embedding template and a serious provider-integration lab

## Generate Locally

```bash
agentpm new ./template-packages/harness-provider-lab/agent.json app-harness-provider-lab
cd app-harness-provider-lab
cp .env.local.example .env.local
pnpm install
pnpm setup:bindings
agentpm harness --json
```

Set `OPENAI_API_KEY` in `.env.local` before the full run. Preflight uses the same environment projection as a run, so it will report the embedding provider unavailable until the key is present.

## Publish Checks

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Template package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/template-packages/harness-provider-lab).
