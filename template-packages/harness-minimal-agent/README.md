# harness-minimal-agent

`harness-minimal-agent` is the smallest Harness starter in this template family.

It generates a workspace that installs one published Agent package, `@zack/devwork-copilot@0.1.6`, and runs that Agent through `agentpm harness`.

## What gets generated

The scaffold includes:

- `README.md`
- `.gitignore`
- `.env.local.example`
- `agentpm.harness.json`
- `agentpm.ollama.harness.json`
- `maintainer-context.md`
- `reports/.gitkeep`
- `tests/test_scaffold.py`

`agentpm new` also synthesizes the generated root `agent.json`, `agent.lock`, and `agentpm.workspace.json`.

## Dependency model

This template has one direct Template dependency:

- `@zack/devwork-copilot@0.1.6`

That Agent package pulls in the rest of the package graph:

- Loop: `@zack/devwork-triage-loop@0.1.0`
- Skill: `@zack/issue-triage-playbook@0.1.0`
- Tool through the Skill: `@zack/github-issues@0.1.1`
- Knowledge: `@zack/devwork-maintainer-guide@0.1.0`
- Memory: `@zack/devwork-maintainer-state@0.1.0`
- Profile: `@zack/devwork-maintainer-style@0.1.0`

The cleaned `devwork-copilot` package intentionally does not depend on `@zack/summarize-text`; that Tool is architecture-sensitive and is not part of this minimal Harness path.

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify file rendering locally before publish:

```bash
agentpm new . ../../harness-minimal-agent-test
```

The full install smoke test requires `@zack/devwork-copilot@0.1.6` and `@zack/harness-minimal-agent@0.1.0` to be published first. After publish:

```bash
agentpm new @zack/harness-minimal-agent my-harness-agent
cd my-harness-agent
agentpm harness --json
```
