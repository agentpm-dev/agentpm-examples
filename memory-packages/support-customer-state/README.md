# support-customer-state

`support-customer-state` is a publishable AgentPM Memory Blueprint package for one durable support-facing customer state document.

It is intentionally the simplest public Memory example in the examples repo. The point of this package is to show that a Memory Blueprint can stay narrow, understandable, and useful without needing multiple spaces or a large lifecycle graph.

Use it for:
- storing durable support preferences for one customer
- carrying stable account context across support sessions
- demonstrating a document-style Memory Blueprint with key retrieval and light lifecycle policy

The package includes:
- [schemas/customer-state.schema.json](schemas/customer-state.schema.json)
- generated contracts under `memory/contracts/` after build
- generated build metadata at `memory/build.json` after build

## Local development

From this directory:

```bash
agentpm lint
agentpm memory build
agentpm memory inspect .
agentpm publish --dry-run
```

The source for this Memory Blueprint can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/memory-packages/support-customer-state).
