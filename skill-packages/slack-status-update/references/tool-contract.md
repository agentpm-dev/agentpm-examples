# Tool Contract Summary

This Skill wraps:

- `@zack/slack-post-message@0.1.1`

Core inputs:

- `action`: `post_message` or `update_message`
- `channel`: Slack channel ID
- `text`: primary message text
- `thread_ts`: optional thread timestamp for replies
- `ts`: message timestamp for update actions

Required environment:

- `SLACK_BOT_TOKEN`

Canonical execution boundary:

```bash
agentpm run @zack/slack-post-message --input '{"action":"post_message","channel":"C123456","text":"hello"}'
```

Helper wrapper:

```bash
./scripts/run.sh '{"action":"post_message","channel":"C123456","text":"hello"}'
./scripts/run.sh --input-file payload.json
```
