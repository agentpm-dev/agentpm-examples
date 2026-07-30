# devwork-maintainer-state

`devwork-maintainer-state` is a publishable AgentPM Memory Blueprint package for maintainer workflow continuity across repository review sessions.

It is intentionally the workflow-oriented Memory example in the examples repo. The point of this package is to show that a Memory Blueprint can hold stable maintainer preferences, active work-thread summaries, and follow-up notes without pretending AgentPM already owns runtime persistence or lifecycle execution.

Use it for:
- storing durable maintainer triage and review preferences
- carrying active repository work threads across review sessions
- keeping follow-up notes and decision cues available until they are acted on
- demonstrating a maintainer-centric lifecycle policy with document and collection spaces

The package includes:
- [schemas/maintainer-preference.schema.json](schemas/maintainer-preference.schema.json)
- [schemas/work-thread.schema.json](schemas/work-thread.schema.json)
- [schemas/follow-up-note.schema.json](schemas/follow-up-note.schema.json)
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

The source for this Memory Blueprint can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/memory-packages/devwork-maintainer-state).
