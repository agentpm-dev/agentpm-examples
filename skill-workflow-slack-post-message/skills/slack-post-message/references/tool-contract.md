# Tool Contract

## Identity

- Package ref: `@zack/slack-post-message`
- Resolved version: `0.1.1`
- Manifest name: `slack-post-message`
- Manifest version: `0.1.1`
- Manifest description: Post or update Slack messages using a compact action surface for agent notifications.

## Environment requirements

- `SLACK_BOT_TOKEN` — required
- `SLACK_API_BASE_URL` — optional, default: `https://slack.com/api`

## Input schema

```json
{
  "additionalProperties": false,
  "properties": {
    "action": {
      "description": "Slack message action to perform.",
      "enum": [
        "post_message",
        "update_message"
      ],
      "type": "string"
    },
    "blocks": {
      "description": "Optional Slack block kit payload.",
      "items": {
        "additionalProperties": true,
        "description": "One Slack block object.",
        "type": "object"
      },
      "type": "array"
    },
    "channel": {
      "description": "Slack channel ID where the message will be posted or updated.",
      "type": "string"
    },
    "text": {
      "description": "Primary message text.",
      "type": "string"
    },
    "thread_ts": {
      "description": "Optional Slack thread timestamp for posting a threaded reply.",
      "type": "string"
    },
    "ts": {
      "description": "Slack timestamp of the message to update.",
      "type": "string"
    }
  },
  "required": [
    "action",
    "channel",
    "text"
  ],
  "type": "object"
}
```

## Output schema

```json
{
  "oneOf": [
    {
      "additionalProperties": false,
      "properties": {
        "action": {
          "description": "Action that was executed.",
          "type": "string"
        },
        "channel": {
          "description": "Slack channel ID returned by Slack.",
          "type": "string"
        },
        "message": {
          "additionalProperties": true,
          "description": "Normalized Slack message payload.",
          "type": "object"
        },
        "metadata": {
          "additionalProperties": true,
          "description": "Additional request metadata such as whether a thread was targeted.",
          "type": "object"
        },
        "ok": {
          "const": true,
          "description": "True when the Slack API call succeeded."
        },
        "ts": {
          "description": "Slack timestamp of the created or updated message.",
          "type": "string"
        }
      },
      "required": [
        "ok",
        "action",
        "channel",
        "ts",
        "message",
        "metadata"
      ],
      "type": "object"
    },
    {
      "additionalProperties": false,
      "properties": {
        "error": {
          "additionalProperties": true,
          "description": "Structured error returned by the tool.",
          "properties": {
            "code": {
              "description": "Stable machine-readable error code.",
              "type": "string"
            },
            "details": {
              "additionalProperties": true,
              "description": "Optional structured context about the failure.",
              "type": "object"
            },
            "message": {
              "description": "Human-readable explanation of the failure.",
              "type": "string"
            }
          },
          "required": [
            "code",
            "message"
          ],
          "type": "object"
        },
        "ok": {
          "const": false,
          "description": "False when validation or the Slack API call failed."
        }
      },
      "required": [
        "ok",
        "error"
      ],
      "type": "object"
    }
  ]
}
```

## Runtime metadata

This is reference/debugging context. In normal use, `agentpm run` should hide these details.

- Runtime: `node (20)`
- Entrypoint command: `node`
- Entrypoint args: `[
  "dist/index.js"
]`
- Entrypoint cwd: `.`
- Timeout (ms): `30000`
