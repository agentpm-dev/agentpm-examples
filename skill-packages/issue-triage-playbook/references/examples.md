# Example Payloads

## List open issues

```json
{
  "action": "list_issues",
  "owner": "agentpm-dev",
  "repo": "agentpm-examples",
  "state": "open",
  "per_page": 20
}
```

## Read one issue

```json
{
  "action": "get_issue",
  "owner": "agentpm-dev",
  "repo": "agentpm-examples",
  "issue_number": 18
}
```

## Draft-only follow-up pattern

Prepare the draft in the agent response first. Only send a write payload when the user explicitly approves it:

```json
{
  "action": "comment_issue",
  "owner": "agentpm-dev",
  "repo": "agentpm-examples",
  "issue_number": 18,
  "body": "Thanks for the report. Are you still able to reproduce this on the latest version?"
}
```
