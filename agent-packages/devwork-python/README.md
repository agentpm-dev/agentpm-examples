# devwork-copilot

`devwork-copilot` is a published AgentPM agent package for maintainer and repository review workflows in Python.

It composes skills for:
- issue triage workflow

It includes Knowledge for:
- maintainer guidance retrieval across triage, labeling, and comment-drafting tasks

It includes Memory for:
- maintainer workflow continuity across profile preferences, active work threads, and follow-up notes

And it keeps direct agent-level tools for:
- summarizing issue queues and maintainer context

Example prompts:
- Review the latest GitHub issues for a repository, group them by theme, and summarize the highest-priority work.
- Read a set of repository issues and produce a concise maintainer briefing with action items and open questions.
- Review an issue thread, retrieve the most relevant maintainer guidance, and draft a short comment that sets expectations clearly.
- Review the current repository issues and summarize what the next maintainer should know, including current priorities, open follow-ups, unresolved questions, and anything that should carry forward.

## Local development

The source code for this agent package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/agent-packages/devwork-python)
