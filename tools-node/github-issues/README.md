# github-issues

Read and update GitHub issues using a compact, agent-friendly action surface.

## Why install it

Issue triage, follow-up, and status workflows are common agent tasks. This tool packages the GitHub issue surface into a small, normalized contract instead of scattering GitHub API glue throughout every agent app.

## Inputs

- `action`: `list_issues`, `get_issue`, `create_issue`, `comment_issue`, or `update_issue_state`
- `owner`: repository owner or organization
- `repo`: repository name
- `issue_number`: issue number for get, comment, or update actions
- `state`: issue state for list or update actions
- `per_page`: maximum number of issues to return for list actions
- `labels`: labels for create actions
- `title`: issue title for create actions
- `body`: issue body or comment body depending on the action

## Outputs

- `action`: executed action name
- `repository`: repository in `owner/repo` form
- `issue`: normalized issue for get, create, or update actions
- `issues`: normalized issue list for list actions
- `comment`: normalized comment for comment actions
- `metadata`: request metadata such as page size or requested state

## Environment variables

- `GITHUB_TOKEN`: required GitHub token
- `GITHUB_API_BASE_URL`: optional API base URL override

## Local development

The source code for this tool can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/tools-node/github-issues)

Test:

```bash
npm test
```

Build:

```bash
npm run build
```

## Example invocation

```bash
printf '%s' '{"action":"list_issues","owner":"octocat","repo":"Hello-World","state":"open"}' | node dist/index.js
```
