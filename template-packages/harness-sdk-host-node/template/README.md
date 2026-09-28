# {{ project_name }}

{{ workspace_label }} is a Node SDK host example for AgentPM Harness.

The app launches `agentpm harness --machine`, registers host services from TypeScript, runs the published `@zack/react-loop` Loop, approves its authored checkpoint, and prints the report summary and trace path at the end.

## Package shape

This template does not install a published Agent package. `agentpm new` creates the root `agent.json` locally in the generated workspace, and that local Agent depends on the published `@zack/react-loop@0.1.0` Loop.

The bindings in `agentpm.harness.json` are runtime-service bindings:

- `node-host-model` is hosted by this Node app
- `sdk-before-model` is the Hook implementation registered by this Node app
- the approval controller is hosted by this Node app

That is the intended SDK-host shape: local Agent, published Loop, app-hosted Harness services.

## What this workspace shows

- `HarnessClient` driving `agentpm harness --machine`
- a Node-hosted ModelRuntime named `node-host-model`
- a `before_model_request` Hook implemented in the app
- a host approval controller for the `approve-next-action` checkpoint in `@zack/react-loop`
- SDK-supplied trusted scope override through `scopes`
- event streaming, usage, report access, and deterministic shutdown
- Ctrl+C cancellation through `cancelRun()`

## Setup

```bash
cp .env.local.example .env.local
pnpm install
```

If you set variables in `.env.local`, the app loads them automatically with `dotenv`.

Useful optional values:

- `AGENTPM=/path/to/agentpm` to run a locally built CLI
- `SDK_HOST_USER={{ default_user_scope }}` to change the user scope sent by the SDK host

## First run

```bash
pnpm dev -- "Use this SDK-hosted Harness example to inspect the generated workspace."
```

The run should finish without external model credentials because the model provider is implemented in `src/main.ts`.

## If it does not run

Start with Harness preflight:

```bash
pnpm dev -- --preflight-only
```

This check goes through the SDK host path, so host model, Hook, and approval services are registered before preflight. If the SDK app cannot find the CLI, set `AGENTPM` in `.env.local`.

## What to inspect

- `src/main.ts` for the hosted model, Hook, approval callback, cancellation handler, and event printing
- `agentpm.harness.json` for the host model/provider/Hook/approval configuration
- `agent.lock` for the installed `@zack/react-loop` dependency
- `reports/` after you add your own `--report` usage or extend the app

## Common next additions

- Add an AgentPM Tool to the local Agent by editing `agent.json`, then run `agentpm install`. To make a Tool available only in one phase, update the Loop package or choose a Loop whose phase access rules expose that Tool only where it should be available.
- Replace the deterministic model provider with a real internal model gateway.
- Add hosted Knowledge, Memory, or embedding providers using the same SDK registration pattern.
- Expand the Hook to inject policy context or reject requests before a provider call.
- Add a second command that runs headless as part of a larger script or CI task.
- Change `trace.content` from `redacted` to `full` only for local debugging; secret-keyed values are still redacted, but full traces can contain more operational detail.

The TUI requires a real interactive terminal. In CI, prefer this SDK machine app or `agentpm harness --headless`.

## Tests

```bash
pnpm test
```
