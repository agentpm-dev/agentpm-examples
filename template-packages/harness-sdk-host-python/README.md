# Harness SDK Host Python

Publishable source for the `@zack/harness-sdk-host-python` workflow template.

This template generates a Python app that launches `agentpm harness --machine` through the Python SDK, registers a host model provider, adds a before-model Hook, approves an authored Loop checkpoint, and prints the resulting report summary and trace location.

Generated apps use a local root `agent.json`. The template does not install a published Agent package; the local Agent depends on the published `@zack/react-loop@0.1.0` Loop, while `agentpm.harness.json` binds runtime services hosted by the Python app.

Before publishing:

```bash
agentpm lint
agentpm publish --dry-run
```

After publishing, smoke the generated app with:

```bash
agentpm new @zack/harness-sdk-host-python app-harness-sdk-host-python
cd app-harness-sdk-host-python
cp .env.local.example .env.local
uv sync
uv run python -m app.main
```
