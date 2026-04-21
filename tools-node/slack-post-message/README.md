# slack-post-message

Post or update Slack messages using a compact action surface for agent notifications.

## Why install it

Many useful agents need to report status or deliver results back to people. This tool gives agents a portable Slack notification primitive instead of custom Slack client code inside every app.

## Inputs

- `action`: `post_message` or `update_message`
- `channel`: Slack channel ID
- `text`: primary message text
- `thread_ts`: optional thread timestamp for replies
- `ts`: message timestamp for update actions
- `blocks`: optional Slack block kit payload

## Outputs

- `action`: executed action name
- `channel`: Slack channel ID
- `ts`: created or updated message timestamp
- `message`: normalized Slack message payload
- `metadata`: request metadata such as whether a thread was targeted

## Environment variables

- `SLACK_BOT_TOKEN`: required bot token
- `SLACK_API_BASE_URL`: optional API base URL override

## Local development

```bash
npm test
```

To build the packaged entrypoint:

```bash
npm run build
```

## Example invocation

```bash
printf '%s' '{"action":"post_message","channel":"C123456","text":"AgentPM Milestone 2 shipped"}' | node dist/index.js
```
