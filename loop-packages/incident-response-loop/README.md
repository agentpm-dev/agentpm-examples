# incident-response-loop

`incident-response-loop` is a publishable AgentPM Loop package for assess, execute, review, and revision-driven incident follow-through.

It packages the portable orchestration contract for a common incident workflow:

- first assess the current incident state and ownership
- then move into active execution when enough context exists
- then review whether the incident can close, needs another execution pass, or should hand off

The goal is to show that a Loop can capture iterative incident control flow without embedding runtime code, provider behavior, or package-specific execution logic.

Use it for:
- demonstrating a clear assess -> execute -> review cycle with a reachable return path into execution
- showing a realistic operations Loop that uses bounded steps, access intent, and fail-phase error handling
- seeding a public incident-response example that fits naturally with the existing ops agent, skill, profile, and memory story

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Loop package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/loop-packages/incident-response-loop).
