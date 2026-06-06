# triage-worker-python

`triage-worker-python` is a published AgentPM workflow template for bootstrapping a Python SDK triage worker project.

It generates a local project that:

- installs the published `@zack/ops-console` agent package through AgentPM
- installs one extra direct tool through the generated root `agent.json`
- loads the published agent with the AgentPM Python SDK
- reads that agent's `resolvedTools` list and loads those tools at runtime
- separately loads the extra direct tool from the generated local manifest

## Runtime story

The intended flow for this template is:

- first run:
  - start with the local incidents fixture included in the scaffold
  - prove the worker can do useful triage without any external credentials
- second step:
  - add `GITHUB_TOKEN` and optionally `SLACK_BOT_TOKEN`
  - let the same worker compare the local incident picture to live GitHub issues or draft Slack-ready updates

So the generated app does not switch between hard-coded modes. It always loads the same installed tools and lets the prompt determine whether the user wants:

- local fixture-first triage
- GitHub-enhanced triage
- or a Slack-ready draft/update flow

## Generated project shape

The scaffold includes:

- `README.md`
- `.env.example`
- `pyproject.toml`
- `app/`
- `fixtures/incidents.csv`
- `tests/test_scaffold.py`

The generated root `agent.json` is synthesized by `agentpm new`, and the generated `agentpm.workspace.json` records the published agent package root.

## Variables

This template currently uses:

- `project_name`
- `worker_label`
- `team_name`
- `input_path`

## Dependency model

This template intentionally demonstrates both dependency paths:

- published agent root:
  - `@zack/ops-console@0.1.0`
- extra direct tool:
  - `@zack/summarize-text@0.1.8`

That means the published agent package still matters here:

- it brings in GitHub, CSV, JSON-transform, and Slack capabilities through `resolvedTools`
- the extra direct tool shows how a generated app can also keep one local manifest-owned dependency alongside that published agent root

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify the scaffold locally before publish:

```bash
agentpm new . ../triage-worker-python-test
```

After publish, generate a test project with:

```bash
agentpm new @zack/triage-worker-python my-triage-app
```
