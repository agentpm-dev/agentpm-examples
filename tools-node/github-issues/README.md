# github-issues

Read and update GitHub issues using a compact, agent-friendly action surface.

Version **0.1.2** declares APDS `agentpm / 1.0.0`. Publish with AgentPM CLI
**0.1.46 or newer**, which includes the declared README in the archive even
when `files` selects only `dist/`. The Tool API is unchanged.

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
pnpm test
```

Build:

```bash
pnpm build
```

## Example invocation

```bash
printf '%s' '{"action":"list_issues","owner":"octocat","repo":"Hello-World","state":"open"}' | node dist/index.js
```

## Publish

Run `pnpm build`, `agentpm lint --strict` and `agentpm publish --dry-run`
before publishing a new version. Sign with a trusted key for your namespace.
Existing immutable releases are not overwritten.
