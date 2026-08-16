# ops-console

`ops-console` is a published AgentPM agent package for operational review, execution, and incident-update workflows in Python.

It includes a Loop for:
- assess -> execute -> review orchestration with a reachable revision cycle and handoff path

It composes skills for:
- incident handoff structure
- Slack status update workflow
- issue triage workflow

It includes Memory for:
- continuity across active operational conversations, incident threads, and handoff context

It includes a Profile for:
- calm, precise incident-operator tone, risk framing, and explicit handoff communication

It includes authored bindings for:
- global and phase-scoped package surfaces
- real Memory Blueprint spaces and operations
- named MCP tool groupings for incident data vs. incident updates
- a consumer-context filename that documents the expected local incident context convention

And it keeps direct agent-level tools for:
- querying CSV data
- transforming JSON payloads

Example prompts:
- Query recent operational data, transform it into a clean summary, and draft a Slack update for the team.
- Inspect recent issues, combine them with structured data, and produce a short operational briefing with next steps.
- Review the current incident state, identify the active owner and open risks, and decide whether the next step is active execution or handoff.
- Review the current incident thread, use the installed continuity memory contract, and summarize what should persist into the next operator handoff.
- Review the current execution result and decide whether the incident can close, needs another execution pass, or should hand off.

## Local development

The source code for this agent package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/ops-python)
