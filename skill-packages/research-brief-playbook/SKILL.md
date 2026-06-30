---
name: research-brief-playbook
description: Multi-step workflow guidance for gathering sources and producing a concise research brief.
---

# Research Brief Playbook

Use this Skill when an agent should move from raw sources to a concise research brief with evidence.

## When to use this Skill

Use it when:
- the user wants a brief grounded in public sources
- there may be multiple source pages or supporting documents
- the agent should gather evidence first and summarize second

Do not use it for speculative brainstorming without source collection.

## Workflow

1. Start with the smallest source set that can answer the question.
2. If a single page is enough, use a direct page extraction path first.
3. If multiple related pages matter, use a bounded crawl.
4. Convert documents and extract tables only when the brief needs them.
5. Summarize only after the useful evidence is already assembled.

## Output standard

Every brief should include:
- the main answer
- the most relevant evidence
- source caveats or missing context
- a short list of follow-up questions when the evidence is incomplete

Use [references/research-brief-template.md](references/research-brief-template.md) as the default format.
Use [references/tool-selection-guide.md](references/tool-selection-guide.md) when deciding which tool should handle the next step.

## Suggested helper paths

Fetch one page:

```bash
./scripts/fetch-page.sh '{"url":"https://example.com/report","format":"markdown"}'
```

Crawl a small site section:

```bash
./scripts/crawl-site.sh '{"url":"https://example.com/research","max_pages":5}'
```

Summarize assembled notes:

```bash
./scripts/summarize-brief.sh '{"text":"<assembled research notes>","style":"concise brief"}'
```

Each helper also accepts:
- `--input-file payload.json`
- no args to fall through to the underlying `agentpm run` command

## Failure cases to avoid

- Summarizing before checking whether the source is authoritative
- Mixing extracted facts with assumptions
- Treating one vendor blog post as conclusive evidence
- Omitting the strongest counterexample or caveat
