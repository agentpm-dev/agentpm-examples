---
name: issue-triage-playbook
description: Procedural guidance for reviewing issue queues, identifying priority, and drafting follow-through.
---

# Issue Triage Playbook

Use this Skill when an agent needs to inspect a GitHub issue queue and turn it into a useful next-step recommendation.

## When to use this Skill

Use it when:
- a repository has multiple open issues and the user wants prioritization help
- the agent should gather the latest issue facts before suggesting work
- a draft follow-up comment is needed before a human approves a write

Do not use this Skill to silently post comments or close issues without an explicit instruction and approval step.

## Triage process

1. Read the relevant issues first.
2. Identify which issues are:
   - blocking users
   - newly regressed
   - missing reproduction detail
   - obviously stale
3. Separate:
   - facts from assumptions
   - draft wording from actions that should actually be executed
4. End with a clear recommendation:
   - address now
   - ask for more detail
   - defer
   - close

## Preferred output

For each issue the agent surfaces, include:
- issue number and short title
- why it matters now
- evidence from the issue body or recent comments
- recommended next step

If the user asks for a comment draft, prepare the draft but do not execute the write unless explicitly told to do so.

## Execution

Read or update issues through the helper script:

```bash
./scripts/run.sh '{"action":"list_issues","owner":"agentpm-dev","repo":"agentpm-examples","state":"open"}'
```

The helper also accepts:
- `./scripts/run.sh --input-file payload.json`
- `./scripts/run.sh` to fall through to plain `agentpm run @zack/github-issues`

See:
- [references/tool-contract.md](references/tool-contract.md)
- [references/triage-decision-cues.md](references/triage-decision-cues.md)
- [references/examples.md](references/examples.md)

## Failure cases to avoid

- Ranking a bug as urgent without citing impact or recency
- Suggesting closure when the issue still has an untested reproduction
- Posting a follow-up comment when the user only asked for a draft
- Treating a maintainer question as resolved work
