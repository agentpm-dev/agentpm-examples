---
name: slack-status-update
description: Workflow guidance for turning operational findings into concise Slack updates.
---

# Slack Status Update

Use this Skill when an agent already has operational findings and needs to communicate them clearly in Slack.

## When to use this Skill

Use it when:
- a team needs a short status update in a shared channel
- an incident thread needs a new progress update
- an already-posted status message should be corrected or refreshed

Do not use it to do the investigation itself. Use it after the important facts are already known.

## Before sending anything

Confirm all of the following:

1. The right destination exists:
   - channel for broad visibility
   - thread for ongoing incident follow-up
2. The message reflects current facts, not guesses.
3. The message contains the next meaningful action, not just the current state.
4. The tone is operational and concise.

## Message structure

Default structure:

- current state
- why it matters
- what changed since the last update
- next action or owner

If the user only asked for a draft, stop at the draft and do not send.

## Execution

Send the final payload with:

```bash
./scripts/run.sh '{"action":"post_message","channel":"C123456","text":"Investigating elevated error rate in checkout. Rollback is in progress. Next update in 15 minutes."}'
```

The helper also accepts:
- `./scripts/run.sh --input-file payload.json`
- `./scripts/run.sh` to fall through to plain `agentpm run @zack/slack-post-message`

For contract details and more examples, see:
- [references/tool-contract.md](references/tool-contract.md)
- [references/examples.md](references/examples.md)

## Common mistakes

- Posting to the channel when the update belongs in an existing thread
- Sending a status note with no next step
- Saying "monitoring" when no concrete owner or trigger is attached
- Updating a message instead of replying when the thread history matters
