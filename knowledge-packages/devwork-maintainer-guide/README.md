# devwork-maintainer-guide

`devwork-maintainer-guide` is a publishable AgentPM Knowledge package for small, authored maintainer workflows that benefit from vector retrieval.

It is intentionally compact. The point of this package is to show a realistic `mode: "vector"` example without hiding behind a large generated corpus.

Use it for:
- retrieving the right triage guidance for a new issue
- looking up labeling rules while reviewing repository queues
- drafting concise maintainer comments that set expectations clearly

This package includes:
- authored maintainer guidance under `knowledge/source-docs/`
- a prepared vector corpus in `knowledge/chunks.jsonl` and `knowledge/sources.jsonl`
- a canonical raw float32 vector payload in `knowledge/embeddings/default.f32`
- build-generated local index metadata after `agentpm knowledge build`

## Local development

From this directory:

```bash
agentpm lint
agentpm knowledge build
agentpm knowledge inspect .
agentpm publish --dry-run
```

The source for this Knowledge package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/knowledge-packages/devwork-maintainer-guide).
