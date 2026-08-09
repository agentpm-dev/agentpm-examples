# ops-console

`ops-console` is a published AgentPM agent package for operational review and update workflows in Python.

It composes skills for:
- incident handoff structure
- Slack status update workflow
- issue triage workflow

It includes Memory for:
- continuity across active operational conversations, incident threads, and handoff context

It includes a Profile for:
- calm, precise incident-operator tone, risk framing, and explicit handoff communication

And it keeps direct agent-level tools for:
- querying CSV data
- transforming JSON payloads

Example prompts:
- Query recent operational data, transform it into a clean summary, and draft a Slack update for the team.
- Inspect recent issues, combine them with structured data, and produce a short operational briefing with next steps.
- Review the current incident thread, use the installed continuity memory contract, and summarize what should persist into the next operator handoff.
- Prepare an incident update that states the current status, open risks, active owner, and next checkpoint in a calm operational tone.

## Local development

The source code for this agent package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/ops-python)
