# devwork-copilot

`devwork-copilot` is a published AgentPM agent package for maintainer and repository review workflows in Python.

Version **0.1.7** adds the exact direct Tool dependency
`@zack/summarize-text@0.1.9`, which uses AgentPM-managed Python dependencies
instead of a bundled environment. Use AgentPM CLI **0.1.37 or newer** and a
Python **3.11+** interpreter for this version.

It includes a Loop for:

- inspect -> draft -> resolve/handoff maintainer orchestration with an explicit revise path back into drafting

It composes skills for:

- issue triage workflow

It includes Knowledge for:

- maintainer guidance retrieval across triage, labeling, and comment-drafting tasks

It includes Memory for:

- maintainer workflow continuity across profile preferences, active work threads, and follow-up notes

It includes a Profile for:

- concise maintainer tone, explicit approval boundaries, and pragmatic follow-through guidance

It includes authored bindings for:

- a shared maintainer behavior profile
- maintainer-state cleanup as a global Memory capability
- phase-scoped Tool, Knowledge, Skill, and Memory surfaces
- a maintainer-specific consumer-context filename

The direct summarizer is available during `inspect-issue` and `draft-comment`.
It can condense supplied issue text or maintainer notes into a requested word
budget. The final `resolve-or-handoff` phase keeps Tool access disabled.

GitHub capability enters through the packaged `issue-triage-playbook` Skill,
which depends on the published `@zack/github-issues` Tool.

Example prompts:

- Review the latest GitHub issues for a repository, group them by theme, and summarize the highest-priority work.
- Read a set of repository issues and produce a concise maintainer briefing with action items and open questions.
- Review an issue thread, retrieve the most relevant maintainer guidance, and draft a short comment that sets expectations clearly.
- Review the current repository issues and summarize what the next maintainer should know, including current priorities, open follow-ups, unresolved questions, and anything that should carry forward.
- Inspect the issue thread, decide whether the next step is to draft a maintainer comment or hand the work off, and explain which packaged loop phase that maps to.
- Review the issue thread, summarize the current maintainer position, and draft the next follow-up comment.

## Local development

The source code for this agent package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/devwork-python)

### Prepare and publish

Publish `@zack/summarize-text@0.1.9` first, using its reviewed author lock, before
publishing this Agent as `@zack/devwork-copilot@0.1.7`. From this directory:

```bash
agentpm lint --strict
agentpm publish --dry-run
agentpm publish --namespace zack
```

Publishing the Agent packages its composition; it does not install its Tools or
create a consumer lock. Keep the existing published Agent versions unchanged.

### Install and verify

After both package versions are published, run these commands from a consumer
workspace. To update the checked-in Harness example, use
`app-harness-minimal-agent/` as that workspace:

```bash
agentpm install @zack/devwork-copilot@0.1.7
export OPENAI_API_KEY='your-key'
agentpm run @zack/summarize-text@0.1.9 --input '{"text":"The maintainer reviewed the bug report, reproduced the problem, and requested a regression test before merging the fix.","max_words":60}'
agentpm harness --json
mkdir -p reports
agentpm harness --headless --input 'During inspection, call summarize-text on this supplied note with a 60-word budget: The maintainer reproduced the bug and requested a regression test before merging. Hand off when the summary is complete.' --report reports/summarizer-check.json
```

Direct execution and Harness model/Tool requests use the OpenAI API and can
incur charges. `GITHUB_TOKEN` is needed only for live GitHub actions; this supplied-text
check does not require fetching an issue. Confirm the report/trace contains
an actual `summarize-text` Tool call rather than only a model-written summary.
The supplied-text check may hand off after inspection without entering later
phases, which can require additional configured capabilities.

Installation updates the workspace's dependency request/portable `agent.lock`
and provisions the summarizer's hash-verified Python environment under
`.agentpm/runtimes/python/`. Review and commit that generated consumer state
after a successful real Registry install. Keep consumer locks/installed package
digests from previously published versions intact until the new versions exist;
do not replace their version strings or invent integrity values by hand.
