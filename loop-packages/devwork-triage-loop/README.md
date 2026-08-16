# devwork-triage-loop

`devwork-triage-loop` is a publishable AgentPM Loop package for slower maintainer review workflows around issue inspection, comment drafting, and explicit resolve-or-handoff decisions.

It packages the portable orchestration contract for a common maintainer pattern:

- first inspect the issue thread and repository context carefully
- then draft the next maintainer-facing follow-up comment
- then decide whether the current pass should resolve, return for another draft, or hand off

The goal is to show that a Loop can capture a review-oriented maintainer workflow without embedding runtime code, provider behavior, or package-specific execution logic.

Use it for:
- demonstrating a slower review/revise maintainer flow distinct from the support and incident examples
- showing explicit outcomes across every phase, including a revision path back into comment drafting
- seeding a public devwork loop that fits naturally with the existing maintainer knowledge, memory, profile, and app story

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Loop package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/loop-packages/devwork-triage-loop).
