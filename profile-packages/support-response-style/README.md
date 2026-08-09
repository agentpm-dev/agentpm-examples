# support-response-style

`support-response-style` is a publishable AgentPM Instruction Profile for calm, direct, customer-facing support communication.

It packages the durable behavioral layer for support responses: role, objectives, tone, formatting guidance, boundaries, and authored constraints. The goal is to keep that behavior portable and inspectable without mixing it into tool logic, workflow code, or Knowledge content.

Use it for:
- drafting customer replies with consistent tone and ownership
- keeping escalation and promise boundaries explicit
- reusing one support-response style across templates, agents, and local apps

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Instruction Profile can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/profile-packages/support-response-style).
