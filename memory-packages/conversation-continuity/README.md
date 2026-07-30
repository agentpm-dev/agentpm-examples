# conversation-continuity

`conversation-continuity` is a publishable AgentPM Memory Blueprint package for durable multi-space conversation state.

It is intentionally the flagship Memory example in the examples repo. The point of this package is to show that a Memory Blueprint can combine ordered history, a durable summary document, and reusable saved notes in one installable contract without pretending AgentPM already hosts the runtime itself.

Use it for:
- retaining recent interaction history with chronological retrieval
- carrying one durable continuity snapshot per active conversation
- storing saved notes or follow-up facts that can be reused across turns
- demonstrating retention, capacity, governance annotations, and declarative lifecycle policy in one package

The package includes:
- [schemas/interaction.schema.json](schemas/interaction.schema.json)
- [schemas/conversation-summary.schema.json](schemas/conversation-summary.schema.json)
- [schemas/saved-note.schema.json](schemas/saved-note.schema.json)
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

The source for this Memory Blueprint can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/memory-packages/conversation-continuity).
