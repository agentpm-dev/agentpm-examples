# react-loop

`react-loop` is a publishable AgentPM Loop package for the established ReAct-style orchestration pattern: reason, act, reflect, and iterate.

It packages a portable control-flow contract for a broadly reusable loop:

- first reason about the current context and decide the next step
- then act through the available execution surface
- then reflect on the result and decide whether to continue, finish, or hand off
- require explicit approval before each action pass begins

The goal is to show that a Loop can capture a widely used agent-control pattern without embedding runtime code, provider behavior, or any one domain's execution model.

Use it for:
- research agents that reason over context before fetching more evidence
- operations agents that need a think -> act -> inspect cycle
- standalone seeding of a public Loop pattern that multiple agents could reuse without being tied to one domain story

The package includes:
- [agent.json](agent.json)
- [README.md](README.md)

## Local development

From this directory:

```bash
agentpm lint
agentpm publish --dry-run
```

The source for this Loop package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/loop-packages/react-loop).
