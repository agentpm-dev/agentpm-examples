# skill-workflow-slack-post-message

Demonstrates the pattern:

- install a published AgentPM tool
- export a starter Skill scaffold
- tailor the Skill for a real workflow
- keep execution delegated to `agentpm run`

This example is intentionally small. It is not a full agent app. The point is to show how a skill-capable client can use a Skill to wrap an installed AgentPM tool without re-implementing the tool contract or runtime handling.

## Pattern

- tool package and runtime stay canonical in AgentPM
- the Skill adds workflow guidance for when and how to use the tool
- `scripts/run.sh` delegates execution back to `agentpm run`
- the same packaged tool can also be exposed through MCP if needed

## Tool

This example uses the published `@zack/slack-post-message` tool.

The tool is a good fit for this pattern because:

- it is already published in AgentPM
- it has a clear, narrow action surface
- it is useful across many agent workflows
- it needs real environment configuration (`SLACK_BOT_TOKEN`)

## Setup

From this directory, install the published tool pinned in `agent.json`:

```bash
agentpm install
```

Required environment variable:

```bash
export SLACK_BOT_TOKEN=xoxb-...
```

Optional:

```bash
export SLACK_API_BASE_URL=https://slack.com/api
```

## Generate the skill scaffold

Export the starter Skill from the installed tool:

```bash
agentpm export --skill @zack/slack-post-message
```

That generates:

```text
skills/slack-post-message/
  SKILL.md
  references/
    tool-contract.md
    examples.md
  scripts/
    run.sh
```

## Files

```text
agent.json
README.md
skills/
  slack-post-message/
    SKILL.md
    references/
      tool-contract.md
      examples.md
    scripts/
      run.sh
```

This example keeps only the setup and guidance in version control. The `skills/slack-post-message/` directory is meant to be generated locally by following the documented flow above.

Once generated, those files show the shape of a tailored Skill:

- `SKILL.md` stays concise and workflow-oriented
- `references/tool-contract.md` keeps manifest-derived details
- `references/examples.md` shows invocation examples
- `scripts/run.sh` delegates to `agentpm run @zack/slack-post-message`

## How an agent would use this

In a skill-capable client, the Skill tells the agent:

- when Slack notification behavior is appropriate
- what inputs are required
- how to choose between `post_message` and `update_message`
- that the actual execution path is the helper script / `agentpm run`

The important part is that the skill does not replace the tool. It tells the agent how to use the tool correctly.

## Why this pattern works

This pattern scales better than exposing every tool contract directly to an agent at once.

- The Skill acts like a manual:
  - when to use the tool
  - how to choose the right arguments
  - what workflow assumptions matter
- `agentpm run` stays the universal execution boundary:
  - the tool contract
  - runtime handling
  - environment defaults
  - subprocess execution
  all stay canonical in AgentPM

That split matters because a JSON schema tells an agent what fields exist, but a Skill tells the agent why to use those fields in a particular workflow.

## Manual command examples

Minimal post:

```bash
./skills/slack-post-message/scripts/run.sh '{"action":"post_message","channel":"C123456","text":"Build succeeded"}'
```

Thread reply:

```bash
./skills/slack-post-message/scripts/run.sh '{"action":"post_message","channel":"C123456","text":"Investigation finished","thread_ts":"1712345678.900000"}'
```

Update an existing message:

```bash
./skills/slack-post-message/scripts/run.sh '{"action":"update_message","channel":"C123456","ts":"1712345678.900000","text":"Build status: green"}'
```

## Relationship to MCP

This repo also demonstrates MCP as another interoperability surface:

```bash
agentpm serve --mcp --tool @zack/slack-post-message
```

The point of this example is that Skill-based workflows and MCP-based workflows can both sit on top of the same packaged AgentPM tool.

## When to use this example

Use this example if you want to show:

- how Skills can wrap installed AgentPM tools
- how to keep workflow guidance separate from tool implementation
- how `agentpm run` can be the execution boundary behind a skill

Do not use this example as a production-ready Slack integration template.
