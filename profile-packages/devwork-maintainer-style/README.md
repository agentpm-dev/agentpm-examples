# devwork-maintainer-style

`devwork-maintainer-style` is a publishable AgentPM Instruction Profile for repository-maintainer triage and follow-through workflows.

It packages the durable behavioral layer for maintainer assistance: role, objectives, tone, formatting guidance, approval boundaries, and authored constraints. The goal is to keep maintainer-facing behavior portable and inspectable across agents and local apps without burying it inside workflow code.

Use it for:
- summarizing issue queues and maintainer priorities
- drafting concise maintainer comments and follow-up notes
- keeping approval-minded write actions explicit in repository workflows

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Instruction Profile can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/profile-packages/devwork-maintainer-style).
