# support-escalation-loop

`support-escalation-loop` is a publishable AgentPM Loop package for support triage, response drafting, and escalation handoff decisions.

It packages the portable orchestration contract for a common support pattern:

- first assess whether the issue can be handled directly
- then draft a customer-facing response when possible
- otherwise move through an explicit escalation review and handoff path

The goal is to show that a Loop can capture durable support control flow without embedding runtime code, provider behavior, or package-specific execution logic.

Use it for:
- demonstrating a support workflow with both direct-resolution and escalation branches
- showing explicit outcomes plus an implicit `complete` phase in one portable Loop
- exercising approval checkpoints, access intent, limits, and error policy in a realistic support example

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Loop package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/loop-packages/support-escalation-loop).
