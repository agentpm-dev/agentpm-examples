# agent-app-support-assistant-workspace

zack-workspace is a multi-agent support workspace generated from the published `@zack/support-assistant-workspace` workflow template.

This template is about workspace structure first, not built-in recursive orchestration.

## What this workspace shows

The generated project includes three different role shapes:

- root `agent.json`
  - synthesized by `agentpm new`
  - the primary local workspace agent
  - owns the direct `@zack/summarize-text` dependency declared by the template
  - includes the published `@zack/support-response-handbook` Knowledge dependency declared by the template
  - includes the published `@zack/support-customer-state` Memory Blueprint declared by the template
- published agent root
  - `@zack/ops-console`
  - recorded in `agentpm.workspace.json`
- local generated agents
  - copied from this template package
  - `agents/answer-drafter.agent.json`
  - `agents/escalation-reviewer.agent.json`

## Important model

This workspace uses the real AgentPM multi-manifest shape:

- root `agent.json`
- local `agents/*.agent.json`
- `agentpm.workspace.json`
- workspace-level `agent.lock`

What it does **not** do:

- it does not add recursive `agents[]` to normal runtime manifests
- it does not assume AgentPM is auto-orchestrating agent-to-agent execution for you

Instead, it gives you a structured project that you can extend with normal application code later.

The template package itself only scaffolds the extra local manifests under `agents/`. The generated root `agent.json` is still synthesized by `agentpm new`.

The generated root agent also carries the published Knowledge package:

- `@zack/support-response-handbook`
  - a context-mode handbook for support-response tone, escalation rules, and reusable message templates

The generated root agent also carries the published Memory package:

- `@zack/support-customer-state`
  - a simple durable support-state document contract for carrying stable customer context across support sessions

## Suggested role breakdown

- root agent:
  - support coordinator / workspace entrypoint
  - direct owner of the installed support-response handbook context package
  - direct owner of the installed support customer state memory package
- published `@zack/ops-console` agent:
  - external operational context and reusable packaged behavior
- local `answer-drafter` agent:
  - workspace-owned drafting / response shaping role
- local `escalation-reviewer` agent:
  - workspace-owned escalation review role

## Setup

```bash
cp .env.example .env.local
agentpm install
uv sync
```

Set:

- `OPENAI_API_KEY`

## Run the illustrative example

```bash
uv run python app/main.py
```

The example code is intentionally minimal. It uses the root workspace tool set and comments to explain how you could grow this workspace into richer orchestration later.
It also prints the installed Knowledge and Memory package details so you can confirm the template-driven dependencies were resolved correctly.

## Sample support thread

The scaffold includes a local support thread at:

```text
sample-inputs/support-thread.md
```

The illustrative script uses that sample file so you can see the workspace in action without Slack or other external credentials.

## How to extend this workspace

Common next steps:

- edit `agents/*.agent.json` to refine local roles
- edit the root `agent.json` to change the coordinator’s direct tools, Knowledge dependencies, or Memory dependencies
- run `agentpm install` after manifest edits to regenerate `agent.lock`
- add normal application code that decides when each local or published agent role should be used

## Files to inspect first

- `agentpm.workspace.json`
- `agent.json`
- `agents/answer-drafter.agent.json`
- `agents/escalation-reviewer.agent.json`
- `app/main.py`
- `pyproject.toml`

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
