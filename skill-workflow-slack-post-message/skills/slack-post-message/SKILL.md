---
name: slack-post-message
description: Post or update Slack messages using a compact action surface for agent notifications.
---

# Slack Post Message

## When to use this skill

- Use it when: Post or update Slack messages using a compact action surface for agent notifications.
- TODO: Add the specific workflow cues that should trigger this skill in your environment.

## Quick start

Run the tool directly:

```bash
agentpm run @zack/slack-post-message --input '{"action":"<action>","channel":"<channel>","text":"Hello world"}'
```

Or use the helper script:

```bash
./scripts/run.sh '{"action":"<action>","channel":"<channel>","text":"Hello world"}'
```

## What this skill covers

- Tool: `@zack/slack-post-message`
- Installed version used for scaffold generation: `0.1.1`

## References

- Tool contract and schema details: [references/tool-contract.md](references/tool-contract.md)
- Example invocations and adaptation ideas: [references/examples.md](references/examples.md)

## Workflow notes

- This skill is a generated starting point. Add workflow-specific guidance before relying on it broadly.
- Keep this file concise and workflow-oriented.
- Put deeper runtime/schema details in the reference files.
- TODO: Add step-by-step workflow guidance specific to your team or repo.
- TODO: Add examples of failure handling, retries, and escalation paths if this tool needs them.
