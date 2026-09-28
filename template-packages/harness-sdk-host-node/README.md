# Harness SDK Host Node

Publishable source for the `@zack/harness-sdk-host-node` workflow template.

This template generates a TypeScript app that launches `agentpm harness --machine` through the Node SDK, registers a host model provider, adds a before-model Hook, approves an authored Loop checkpoint, and prints the resulting report summary and trace location.

Generated apps use a local root `agent.json`. The template does not install a published Agent package; the local Agent depends on the published `@zack/react-loop@0.1.0` Loop, while `agentpm.harness.json` binds runtime services hosted by the Node app.

Before publishing:

```bash
agentpm lint
agentpm publish --dry-run
```

After publishing, smoke the generated app with:

```bash
agentpm new @zack/harness-sdk-host-node app-harness-sdk-host-node
cd app-harness-sdk-host-node
cp .env.local.example .env.local
pnpm install
pnpm dev
```
