# Tool Contract Summary

This Skill wraps:

- `@zack/github-issues@0.1.1`

Core actions:

- `list_issues`
- `get_issue`
- `create_issue`
- `comment_issue`
- `update_issue_state`

Required baseline inputs:

- `action`
- `owner`
- `repo`

Often-needed action-specific inputs:

- `issue_number` for read, comment, or update actions
- `state` for list or update actions
- `title` and `body` for create actions
- `body` for comment actions

Required environment:

- `GITHUB_TOKEN`

Canonical execution boundary:

```bash
agentpm run @zack/github-issues --input '{"action":"list_issues","owner":"agentpm-dev","repo":"agentpm-examples","state":"open"}'
```

Helper wrapper:

```bash
./scripts/run.sh '{"action":"list_issues","owner":"agentpm-dev","repo":"agentpm-examples","state":"open"}'
./scripts/run.sh --input-file payload.json
```

Important workflow note:

- read actions are safe defaults for triage
- write actions should usually be drafted first and only executed after explicit user approval
