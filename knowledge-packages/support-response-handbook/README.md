# support-response-handbook

`support-response-handbook` is a publishable AgentPM Knowledge package for direct context loading in support workflows.

It is intentionally a multi-file `mode: "context"` example. The point of this package is to show that a Knowledge artifact can bundle reusable operational guidance without pretending that every retrieval problem needs embeddings or vector search.

Use it for:
- drafting customer-facing replies with a consistent tone
- deciding when a thread should be escalated or handed off
- keeping response templates and support principles packaged together as one installable artifact

The package includes:
- [knowledge/docs/response-principles.md](knowledge/docs/response-principles.md)
- [knowledge/docs/escalation-guidelines.md](knowledge/docs/escalation-guidelines.md)
- [knowledge/docs/message-templates.md](knowledge/docs/message-templates.md)
- [knowledge/provenance/sources-manifest.json](knowledge/provenance/sources-manifest.json)

## Local development

From this directory:

```bash
agentpm lint
agentpm knowledge build
agentpm knowledge inspect .
agentpm publish --dry-run
```

The source for this Knowledge package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/knowledge-packages/support-response-handbook).
