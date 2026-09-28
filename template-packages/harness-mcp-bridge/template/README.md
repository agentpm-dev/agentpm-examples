# {{ project_name }}

{{ workspace_label }} is a Harness MCP bridge workspace.

It shows two different MCP directions that are easy to confuse:

- **Harness-managed exports:** your authored AgentPM Tool dependencies can be exposed to external MCP clients by Harness.
- **Runtime imports:** Harness augments a Run with an external MCP server configured in `agentpm.harness.json`.

Those are separate surfaces. `mcp.exports` publishes selected AgentPM tools outward from Harness. `mcp.imports` makes external MCP tools available inside Harness Runs.

## Package Shape

This template does not install a published Agent package. `agentpm new` creates the root `agent.json` locally in the generated workspace. That local Agent depends on:

- `@zack/react-loop@0.1.0`
- `@zack/csv-query@0.1.4`
- `@zack/json-transform@0.1.1`

`scripts/configure-agent-bindings.mjs` adds this outward MCP export binding to the generated root Agent:

- export id `authored-tools`
- tools `@zack/csv-query` and `@zack/json-transform`

Harness-managed MCP exports use that `bindings.mcp` surface.

`agentpm.harness.json` configures one inward MCP import:

- import id `bridge-search`
- HTTP endpoint `http://127.0.0.1:18241/mcp`
- imported tool `lookup`
- scope `act` only
- `Authorization` header projected from `MCP_BRIDGE_AUTHORIZATION`

## Setup

```bash
cp .env.local.example .env.local
pnpm install
pnpm setup:bindings
```

The checked-in `.env.local.example` uses a local placeholder credential for the fixture server:

```text
MCP_BRIDGE_AUTHORIZATION=Bearer local-mcp-bridge-token
```

For a real remote MCP server, put the real credential in `.env.local` or your shell environment. Do not put bearer tokens, API keys, cookies, passwords, or private keys in `agentpm.harness.json`, package metadata, `model.options`, or phase outputs.

## First Run: Harness Import

The local HTTP MCP import server must be running before Harness preflight. The package scripts start it for you.

Check readiness:

```bash
pnpm harness:json
```

Run one headless prompt:

```bash
pnpm run harness:headless -- "Use the MCP bridge to verify the imported lookup tool."
```

The successful run should include:

- `mcp:bridge-search/lookup` available only in phase `act`
- one external MCP tool invocation
- one auto-approved checkpoint before `act`
- terminal output confirming the imported lookup result

## TUI Run

For the TUI, start the MCP fixture server in a second terminal:

```bash
pnpm mcp:server
```

Then open Harness:

```bash
agentpm harness
```

## Harness MCP Export

Harness starts the configured `mcp.exports` surfaces for TUI and machine/SDK-hosted Harness sessions, and for the duration of a headless Run. That is useful when a long-lived Harness session should also make the Agent's authored tools available to MCP clients.

This template configures one export surface:

- export id `authored-tools`
- exported tools `@zack/csv-query` and `@zack/json-transform`

The standalone `agentpm serve --mcp` command is separate from Harness-managed exports. It serves locked Tool packages from `agent.lock` by default, and can be filtered with `--tool` or `--tools` when you want a standalone MCP server.

## If It Does Not Run

Run:

```bash
pnpm harness:json
```

If the MCP import is unavailable, check:

- `.env.local` exists and contains `MCP_BRIDGE_AUTHORIZATION`
- no other process is using port `18241`
- `agentpm.harness.json` still points at `http://127.0.0.1:18241/mcp`
- `mcp.imports.bridge-search.scope.phases` includes `act`

Credentials should stay in `.env.local` or your shell environment. Secret-keyed values are redacted in reports, traces, prompts, and stdout, including when trace content is `full`.

## Common Next Additions

- Point `mcp.imports.bridge-search.url` at your real remote MCP server.
- Replace the local placeholder `MCP_BRIDGE_AUTHORIZATION` with a real secret in `.env.local`.
- Add another MCP import with a different phase scope so only specific Loop phases can call it.
- Add more authored tools to `bindings.mcp` when you want Harness-managed MCP exports to publish additional AgentPM packages.
- Run headless from a larger script with `agentpm harness --headless --input ... --report ...`.
- Change `trace.content` from `redacted` to `full` only for local debugging; full traces include more operational detail, but secret-keyed values are still redacted.

The TUI requires a real interactive terminal. In CI, prefer `pnpm run harness:headless`.

## Tests

```bash
pnpm test
```
