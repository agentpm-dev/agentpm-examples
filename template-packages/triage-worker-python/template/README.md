# {{ project_name }}

{{ worker_label }} is a local Python SDK triage console for the {{ team_name }} team.

It was generated from the published `@zack/triage-worker-python` workflow template and shows two AgentPM dependency paths in one app:

- a published agent package root recorded in `agentpm.workspace.json`
- one extra direct tool declared in the generated root `agent.json`

## How to use this app

This scaffold is designed around two progressively richer paths:

- fixture-first triage:
  - start with the bundled local incident file at `{{ input_path }}`
  - verify the worker can summarize, prioritize, and draft updates without any external credentials
- GitHub and Slack follow-on:
  - once `GITHUB_TOKEN` and optionally `SLACK_BOT_TOKEN` are set, ask the same worker to compare the local incident picture with live GitHub issues or draft/send Slack-ready updates

The code does not use separate hard-coded modes. It always loads the same installed tools and uses your prompt to decide whether to stay local or bring in live GitHub/Slack context.

## What this app does

This app:

- loads the published `@zack/ops-console` agent package with the AgentPM Python SDK
- reads the agent's direct resolved tools, then loads its resolved Skill packages and the Skills' resolved tools dynamically
- separately loads the direct `@zack/summarize-text` tool from the generated local manifest
- runs an interactive LangChain-managed triage loop over local incident data, GitHub issues, JSON transforms, and optional Slack updates

## Setup

```bash
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

## Fixture-first workflow

This scaffold includes a local incident fixture at:

```text
{{ input_path }}
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

- `Look at {{ input_path }}, identify the highest-severity open incidents, and give me a short {{ team_name }} triage summary.`
- `Use the local incidents fixture at {{ input_path }}, draft a calm status update for the {{ team_name }} team, and do not send it anywhere yet.`
- `Summarize the main operational risks in {{ input_path }} and tell me which follow-up items should happen first.`
- `Using the columns incident_id, severity, status, opened_at, and summary from {{ input_path }}, summarize the most urgent open incidents.`
- `If GitHub credentials are available, list open issues in agentpm-dev/agentpm-examples and compare them to the incidents in {{ input_path }}.`
- `If GitHub credentials are available, compare the incidents in {{ input_path }} to open repo issues and tell me what looks under-reported.`
- `If Slack credentials are available, draft a Slack update from the incidents in {{ input_path }} but do not send it yet.`

## Tests

```bash
uv run python -m unittest discover -s tests -p 'test_*.py'
```
