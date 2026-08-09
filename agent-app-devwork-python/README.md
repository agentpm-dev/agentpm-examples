# agent-app-devwork-python

Interactive local GitHub maintainer copilot built on the AgentPM Python SDK and an explicit LangGraph workflow.

## What it does

This app installs the published `devwork-copilot` agent package, loads it with the AgentPM Python SDK, and uses the direct tools and Skill-backed tools resolved for that agent inside a graph-driven devwork loop.

Published agent package:

- `@zack/devwork-copilot@0.1.4`

Package source:

- [`agent-packages/devwork-python`](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/devwork-python)

## Pattern

This example shows a real app that:

- installs a published agent package
- loads that agent with `load_agent(...)`
- reads direct `resolvedTools` from the agent
- reads `resolvedSkills`, loads those Skills with `load_skill(...)`, and then loads each Skill's `resolvedTools`
- reads `resolvedKnowledge`, loads the installed Knowledge package with `load_knowledge(...)`, and exposes the vector package metadata in the terminal banner
- reads `resolvedMemory`, loads the installed `@zack/devwork-maintainer-state` Memory Blueprint, and exposes its installed spaces, lifecycle operations, and contract summary in the terminal banner
- reads `resolvedProfiles`, loads the installed `@zack/devwork-maintainer-style` Instruction Profile, and exposes its role, objectives, constraints, and tone in the terminal banner
- feeds the loaded Skill manual into the workflow prompt
- feeds the loaded Instruction Profile metadata into the workflow prompt
- runs a stateful maintainer workflow against real installed packages

- orchestration style: LangGraph state machine with guarded transitions
- runtime: Python
- best for: showing explicit workflow state, approval gates, and safer write-capable agent behavior

## Expected agent install

From this app directory, install the published agent package:

```bash
agentpm install @zack/devwork-copilot@0.1.4
```

That should install:

- the agent artifact under `.agentpm/agents/...`
- the resolved Knowledge artifact under `.agentpm/knowledge/...`
- the resolved Memory artifact under `.agentpm/memory/...`
- the resolved Profile artifact under `.agentpm/profiles/...`
- the resolved Skill artifact under `.agentpm/skills/...`
- the resolved tool artifacts under `.agentpm/tools/...`

## Setup

From this app directory:

```bash
uv sync
```

This example requires `agentpm>=0.1.11` so the Python SDK can load installed Knowledge, Memory, and Profile packages with `load_knowledge(...)`, `load_memory(...)`, and `load_profile(...)`.

## Environment

Create a local env file:

```bash
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL`
- `GITHUB_TOKEN`

## Run

```bash
cd agent-app-devwork-python
uv run python -m dotenv -f .env.local run -- python -m app.main
```

## Run tests

```bash
cd agent-app-devwork-python
uv run python -m unittest discover -s tests -p 'test_*.py'
```

## REPL commands

- `/help`: show commands
- `/tools`: list loaded tools
- `/approve`: execute the currently pending GitHub write action
- `/cancel`: discard the currently pending GitHub write action
- `/reset`: clear conversation history and pending actions
- `/quit`: exit

## Example prompts

- `List the open issues in agentpm-dev/agentpm-examples and tell me which one should be handled first.`
- `Review open issues in agentpm-dev/agentpm-examples and draft a maintainer comment for the most recent one asking whether it is still reproducible.`
- `Look at issue #18 in agentpm-dev/agentpm-examples and propose a concise follow-up comment, but do not post it yet.`
- `Comment on issue #18 that it should be resolved now.`

For write requests, the app should stop and ask for `/approve` before executing the GitHub mutation.

## Notes

- This app intentionally uses an explicit graph with state and guarded transitions so it contrasts with the other example orchestration styles.
- GitHub write actions are gated behind explicit user approval.
- The graph keeps local conversational state across turns until `/reset`.
- Tool calls and tool outputs are logged so the execution path is easy to inspect.
- The current published agent package brings in `issue-triage-playbook`, so the workflow prompt includes the packaged triage manual as part of its maintainer guidance.
- The current published agent package also brings in `devwork-maintainer-guide`, and the banner prints its installed vector-mode metadata so you can confirm the Knowledge dependency was resolved correctly.
- The current published agent package also brings in `devwork-maintainer-state`, and the banner prints its installed Memory Blueprint metadata so you can confirm the Memory dependency was resolved correctly.
- The current published agent package also brings in `devwork-maintainer-style`, and the banner prints its installed Instruction Profile metadata so you can confirm the Profile dependency was resolved correctly.
