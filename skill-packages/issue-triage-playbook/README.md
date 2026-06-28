# issue-triage-playbook

`issue-triage-playbook` is a publishable AgentPM Skill package for issue review and follow-up workflows.

It depends on:
- `@zack/github-issues`

Use it for:
- reviewing the current open issue queue
- deciding which issue needs attention first
- drafting a follow-up comment before any write action is taken
- deciding whether a queue needs grouping, escalation, or closure work

## Files

- [SKILL.md](SKILL.md): issue triage workflow guidance
- [references/tool-contract.md](references/tool-contract.md): compact tool contract summary
- [references/triage-decision-cues.md](references/triage-decision-cues.md): priority and follow-up cues
- [references/examples.md](references/examples.md): example read/write payloads
- [scripts/run.sh](scripts/run.sh): thin wrapper that delegates to `agentpm run` with inline JSON, `--input-file`, or plain passthrough

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Skill package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/skill-packages/issue-triage-playbook).
