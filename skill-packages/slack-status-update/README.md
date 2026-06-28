# slack-status-update

`slack-status-update` is a publishable AgentPM Skill package for drafting and sending concise operational Slack updates.

This package is the concrete export-to-publish example in this repo. It starts from the `agentpm export --skill` pattern, but the result here is a real Skill source package that can be linted and published.

It depends on:
- `@zack/slack-post-message`

Use it for:
- posting a short incident update to a channel
- replying in an existing incident thread
- updating an already-posted message when the situation changes

## Files

- [SKILL.md](SKILL.md): workflow guidance
- [references/tool-contract.md](references/tool-contract.md): compact tool contract summary
- [references/examples.md](references/examples.md): invocation examples and message patterns
- [scripts/run.sh](scripts/run.sh): thin wrapper that delegates to `agentpm run` with inline JSON, `--input-file`, or plain passthrough

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Skill package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/skill-packages/slack-status-update).
