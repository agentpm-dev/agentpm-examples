# research-brief-playbook

`research-brief-playbook` is a publishable AgentPM Skill package for structured research workflows.

It depends on the existing research tool stack:
- `@zack/web-page-extract`
- `@zack/robots-aware-crawl`
- `@zack/document-convert`
- `@zack/table-extract`
- `@zack/markdown-chunk`
- `@zack/summarize-text`

This package is intentionally a multi-tool Skill. The point is to show that a Skill can capture a repeatable workflow across several tools without turning into a separate app runtime.

## Files

- [SKILL.md](SKILL.md): the actual research workflow
- [references/research-brief-template.md](references/research-brief-template.md): default output structure
- [references/source-quality-checks.md](references/source-quality-checks.md): source and evidence rules
- [references/tool-selection-guide.md](references/tool-selection-guide.md): when to choose each tool in the stack
- [scripts/fetch-page.sh](scripts/fetch-page.sh): thin helper around `web-page-extract`
- [scripts/crawl-site.sh](scripts/crawl-site.sh): thin helper around `robots-aware-crawl`
- [scripts/summarize-brief.sh](scripts/summarize-brief.sh): thin helper around `summarize-text`

Each helper accepts:
- an inline JSON payload
- `--input-file <path>`
- or no args to fall through to plain `agentpm run`

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Skill package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/skill-packages/research-brief-playbook).
