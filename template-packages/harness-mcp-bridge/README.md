# harness-mcp-bridge

`harness-mcp-bridge` is a publishable AgentPM workflow template for users who want to see both MCP directions inside Harness:

- Harness-managed exports from authored AgentPM Tool dependencies
- inward runtime augmentation from a scoped external HTTP MCP import inside `agentpm harness`

Generated apps depend on published packages:

- `@zack/react-loop@0.1.0`
- `@zack/csv-query@0.1.4`
- `@zack/json-transform@0.1.1`

## What It Demonstrates

- authored AgentPM Tool exports through `bindings.mcp`
- Harness HTTP MCP import configuration with explicit phase scope
- MCP HTTP credential handling with `{ "env": "MCP_BRIDGE_AUTHORIZATION" }`
- a local fixture MCP server for repeatable preflight and headless runs
- a deterministic process ModelRuntime that calls the imported MCP tool

Harness-managed MCP exports use the generated Agent's `bindings.mcp` surface. The generated README keeps standalone `agentpm serve --mcp` as an optional note; it is not part of the primary template flow.

## Generate Locally

```bash
agentpm new ./template-packages/harness-mcp-bridge/agent.json app-harness-mcp-bridge
cd app-harness-mcp-bridge
cp .env.local.example .env.local
pnpm install
pnpm setup:bindings
pnpm harness:json
```

## Publish Checks

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Template package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/template-packages/harness-mcp-bridge).
