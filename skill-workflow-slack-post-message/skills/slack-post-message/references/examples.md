# Examples

These examples are generated starters. Adjust them to match the real workflow this skill should support.

## Inline JSON

```bash
agentpm run @zack/slack-post-message --input '{"action":"<action>","channel":"<channel>","text":"Hello world"}'
```

## stdin JSON

```bash
cat <<'JSON' | agentpm run @zack/slack-post-message
{
  "action": "<action>",
  "blocks": [],
  "channel": "<channel>",
  "text": "Hello world"
}
JSON
```

## Expanded example

Use this when you want to show optional fields and richer tool behavior:

```json
{
  "action": "<action>",
  "blocks": [],
  "channel": "<channel>",
  "text": "Hello world",
  "thread_ts": "<thread_ts>",
  "ts": "<ts>"
}
```

## Helper script

```bash
./scripts/run.sh '{"action":"<action>","blocks":[],"channel":"<channel>","text":"Hello world","thread_ts":"<thread_ts>","ts":"<ts>"}'
```

## TODOs

- TODO: Add one realistic example from your actual workflow.
- TODO: Add examples for invalid input or failure cases if this tool is safety-sensitive.
- TODO: Note any required environment variables or credentials that should be set before running the tool.
