# incident-handoff-checklist

`incident-handoff-checklist` is a publishable AgentPM Skill package for operational handoffs.

It is intentionally procedural-only. The point of this package is to show that a Skill can capture reusable know-how even when there is no tool to execute.

Use it for:
- incident status handoffs between teammates or shifts
- drafting a concise operational update before paging in another team
- making sure ownership, next step, and risk are explicit before an agent stops

The core manual lives in [SKILL.md](SKILL.md). A reusable handoff skeleton lives in [references/handoff-template.md](references/handoff-template.md).

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Skill package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/skill-packages/incident-handoff-checklist).
