# support-assistant-workspace

`support-assistant-workspace` is a published AgentPM workflow template for bootstrapping a multi-manifest support workspace.

It generates a local project that:

- synthesizes the root `agent.json` as a normal single-agent manifest
- installs a published context-mode Knowledge package for support-response guidance
- adds extra local agent manifests under `agents/`
- records a published agent root in `agentpm.workspace.json`
- writes a workspace-level `agent.lock`
- includes a small Python entrypoint plus `pyproject.toml` for the workspace example
- gives users a structured starting point for future app-level orchestration without pretending AgentPM already has recursive agent orchestration semantics

## Workspace shape

The generated project includes:

- root `agent.json`
- `agentpm.workspace.json`
- `agent.lock`
- `agents/answer-drafter.agent.json`
- `agents/escalation-reviewer.agent.json`
- `app/main.py`
- `sample-inputs/support-thread.md`

## Published and local roles

This template intentionally combines:

- a published Knowledge package:
  - `@zack/support-response-handbook@0.1.0`
- a published agent root:
  - `@zack/ops-console@0.1.1`
- local generated agents:
  - `answer-drafter`
  - `escalation-reviewer`

That demonstrates the real AgentPM workspace model:

- template-declared Knowledge dependencies are installed and synthesized into the generated root `agent.json`
- published agent roots live in `agentpm.workspace.json`
- local agents live under `agents/`
- normal `kind: "agent"` manifests do not gain recursive `agents[]`

## Variables

This template currently uses:

- `project_name`
- `workspace_label`
- `sample_thread_path`

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify the scaffold locally before publish:

```bash
agentpm new . ../support-assistant-workspace-test --var workspace_label="Support Workspace"
```

After publish, generate a test project with:

```bash
agentpm new @zack/support-assistant-workspace my-support-workspace --var workspace_label="Support Workspace"
```
