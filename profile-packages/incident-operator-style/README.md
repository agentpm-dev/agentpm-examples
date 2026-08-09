# incident-operator-style

`incident-operator-style` is a publishable AgentPM Instruction Profile for incident and operations coordination.

It packages the durable behavioral layer for operational updates: role, objectives, tone, formatting guidance, handoff boundaries, and authored constraints. The goal is to make incident-response communication portable and inspectable across agents, templates, and local apps without burying it inside workflow code.

Use it for:
- preparing operational triage summaries
- drafting incident status updates with explicit ownership and risk framing
- carrying a consistent handoff style across shift changes or escalation workflows

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Instruction Profile can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/profile-packages/incident-operator-style).
