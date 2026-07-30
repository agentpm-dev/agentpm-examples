# agent-app-ops-python

zack-worker is a local Python SDK triage console for the Operations team.

It was generated from the published `@zack/triage-worker-python` workflow template and shows two AgentPM dependency paths in one app:

- a published agent package root recorded in `agentpm.workspace.json`
- one extra direct tool declared in the generated root `agent.json`

## How to use this app

This scaffold is designed around two progressively richer paths:

- fixture-first triage:
  - start with the bundled local incident file at `fixtures/incidents.csv`
  - verify the worker can summarize, prioritize, and draft updates without any external credentials
- GitHub and Slack follow-on:
  - once `GITHUB_TOKEN` and optionally `SLACK_BOT_TOKEN` are set, ask the same worker to compare the local incident picture with live GitHub issues or draft/send Slack-ready updates

The code does not use separate hard-coded modes. It always loads the same installed tools and uses your prompt to decide whether to stay local or bring in live GitHub/Slack context.

## What this app does

This app:

- loads the published `@zack/ops-console` agent package with the AgentPM Python SDK
- reads the agent's direct `resolvedTools`
- reads the agent's `resolvedSkills`, loads those Skill packages with `load_skill(...)`, and then loads each Skill's `resolvedTools`
- reads the agent's `resolvedMemory`, loads the published `@zack/conversation-continuity` Memory Blueprint, and prints its installed spaces, lifecycle operations, and contract summary at startup
- feeds the loaded Skill manuals into the agent prompt so the runtime follows the packaged procedures as well as the packaged tool graph
- separately loads the direct `@zack/summarize-text` tool from the generated local manifest
- runs an interactive LangChain-managed triage loop over local incident data, GitHub issues, JSON transforms, and optional Slack updates

## Setup

```bash
agentpm install
uv sync
cp .env.example .env.local
```

Set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL`
- optionally `GITHUB_TOKEN` if you want live GitHub issue access
- optionally `SLACK_BOT_TOKEN` if you want to send Slack updates

## Run

```bash
uv run python -m dotenv -f .env.local run -- python -m app.main
```

`agentpm install` restores the published agent root and direct tool dependency into `.agentpm/` from the checked-in `agent.json`, `agent.lock`, and `agentpm.workspace.json`.

With the current published `@zack/ops-console` package, that means:

- direct agent tools like `csv-query` and `json-transform` load from the agent's own `resolvedTools`
- Skill packages like incident handoff, Slack status updates, and issue triage load from `resolvedSkills`
- the published `@zack/conversation-continuity` Memory Blueprint loads from `resolvedMemory` so you can inspect the installed continuity contract for conversation state and saved notes
- tool-backed Skills then contribute their own resolved tool refs such as GitHub issue access and Slack posting

## Fixture-first workflow

This scaffold includes a local incident fixture at:

```text
fixtures/incidents.csv
```

That gives you a low-friction path to try the worker before you wire it to live systems.

The fixture columns are:

- `incident_id`
- `service`
- `severity`
- `status`
- `owner`
- `opened_at`
- `region`
- `summary`

When using `csv-query` against this fixture:

- use those exact column names
- use filter ops like `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, or `contains`
- do not use symbolic operators like `=`

## Example prompts

- `Look at fixtures/incidents.csv, identify the highest-severity open incidents, and give me a short Operations triage summary.`
- `Use the local incidents fixture at fixtures/incidents.csv, draft a calm status update for the Operations team, and do not send it anywhere yet.`
- `Summarize the main operational risks in fixtures/incidents.csv and tell me which follow-up items should happen first.`
- `Review the open incidents in fixtures/incidents.csv and prepare the next handoff with the current status, open risks, recent decisions, and anything that should carry forward.`
- `Using the columns incident_id, severity, status, opened_at, and summary from fixtures/incidents.csv, summarize the most urgent open incidents.`
- `If GitHub credentials are available, list open issues in agentpm-dev/agentpm-examples and compare them to the incidents in fixtures/incidents.csv.`
- `If GitHub credentials are available, compare the incidents in fixtures/incidents.csv to open repo issues and tell me what looks under-reported.`
- `If Slack credentials are available, draft a Slack update from the incidents in fixtures/incidents.csv but do not send it yet.`

## Tests

```bash
agentpm install
uv run python -m unittest discover -s tests -p 'test_*.py'
```
