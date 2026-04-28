# `agentpm-examples` Repo Guide

This repo exists to prove ecosystem value, not just to demonstrate mechanics. It should show that AgentPM tools and agent apps are installable, understandable, and useful across runtimes.

## Local Rules
- Examples are for demonstration and learning, not production use.
- Node workspaces are managed with `pnpm`.
- Python tools and apps use `uv`.
- Manifests are contract surfaces; keep `agentpm lint` in the loop whenever `agent.json` changes.
- The current recommended agent apps are `agent-app-research-node`, `agent-app-ops-python`, and `agent-app-devwork-python`; older `agent-app-node` and `agent-app-python` are legacy examples and should not be treated as the main pattern by default.

## Builder Guidance
- Prefer examples that prove reusable value over examples that only demonstrate abstraction.
- Keep tools installable, testable, and publishable in the documented AgentPM flow.
- Keep agent apps sturdy and legible; orchestration style should be obvious from the code and the terminal output.
- Preserve the mixed Node/Python credibility of the repo.
- Prefer narrow, localized diffs.
- Avoid overcomplicating examples when a simpler proof is stronger.
- Update tests and READMEs when behavior changes.
- If a change materially affects how users understand AgentPM, update the public docs in the API repo’s top-level `docs/` content system when that repo is available.
- Optimize examples for copy/paste learning: clear commands, minimal hidden setup, obvious env vars, and predictable terminal output.
- When an example requires environment variables, document them in the README and keep any `.env.example` file in sync.
- Never commit real secrets or user-specific tokens.
- Avoid repo-local shortcuts that make the example impossible to understand outside this repo.
- Prefer documented AgentPM install/load flows over private local wiring unless the example is explicitly about local development.

## Important Files And Contract Surfaces
- `README.md`: top-level explanation of the repo’s example set and the current recommended agent patterns.
- `pnpm-workspace.yaml`: Node workspace boundary for `tools-node/*` and `agent-app-*`.
- `tools-node/*/agent.json`, `tools-python/*/agent.json`: tool manifest contract surfaces.
- `agent-app-*/agent.json`: app tool-dependency contract surfaces.
- `agent-app-*/agent.lock`: resolved install contract for example apps.
- Tool READMEs and app READMEs: documented setup, install, test, and run flows must remain truthful.
- Representative current apps:
  - `agent-app-research-node`: manual OpenAI tool-calling loop
  - `agent-app-ops-python`: LangChain-managed tools agent
  - `agent-app-devwork-python`: LangGraph workflow with approval gating

## Common Patterns In This Repo
- A real tool example usually includes code, tests, a README, and `agent.json`.
- Node tools usually package a bundled or explicit runtime artifact with a Node entrypoint.
- Python tools usually use lightweight package layouts with a direct `python -u .../__main__.py` entrypoint or similar package execution model.
- Agent apps load tools from local `agent.json` and usually keep `agent.lock` alongside them.
- The strongest examples show installable value, not just conceptual possibility.
- Tool/app READMEs are part of the product of the example, not optional documentation afterthoughts.
- Example output should be understandable without reading the entire implementation first.

## Common Workflows

### When adding or changing a tool
1. Start in the tool directory under `tools-node/*` or `tools-python/*`.
2. Update the implementation, tests, README, and `agent.json` together.
3. Run `agentpm lint` in the tool root after manifest edits.
4. Verify the tool’s documented local test command still works.
5. Decide whether the tool should also be consumed by one of the current agent apps.

Example:
- A Python tool like `tools-python/csv-query` uses `agent.json`, a lightweight package directory, and explicit unit tests; that whole shape is part of the example contract.

### When adding or changing an agent app
1. Keep the orchestration style explicit and intentional.
2. Load tools through the SDKs in the documented AgentPM flow when possible.
3. Keep `agent.json`, `agent.lock`, and the README in sync.
4. Make tool selection, invocation, and results legible to the user.
5. Be clear whether the app is a current recommended pattern or a legacy example.

Example:
- `agent-app-research-node` is intentionally a direct OpenAI tool-calling example, while `agent-app-devwork-python` is intentionally a LangGraph workflow example; preserve that contrast when changing them.

### When changing manifests or install flows
1. Treat `agent.json` as the source of truth for tool/app packaging intent.
2. Run `agentpm lint` after manifest edits.
3. Check whether `agent.lock` or documented install steps also need to change.
4. If the manifest change alters what users learn about AgentPM, update the local README and consider whether `agentpm-api/docs` should change too.

### When changing README instructions
1. Treat README commands as executable claims, not aspirational guidance.
2. Keep setup, install, build, test, and run commands in sync with the code.
3. Prefer `pnpm` for Node examples and `uv` for Python examples unless there is already a repo-local exception.

### When a completed spec might be blog-worthy
1. Ask whether the example proves a broader AgentPM point, not just a local implementation detail.
2. If yes, leave behind useful material in `blog-brief.md` for the blog pipeline.

## Decision Guide

| If the change is about... | Start here | Also inspect |
|---|---|---|
| a Node tool | matching `tools-node/*` package | `agent.json`, README, tests, package/build config |
| a Python tool | matching `tools-python/*` package | `agent.json`, README, tests, `pyproject.toml` |
| a current recommended agent app | matching `agent-app-research-node`, `agent-app-ops-python`, or `agent-app-devwork-python` | `agent.json`, `agent.lock`, README, orchestration code |
| a legacy agent app | matching `agent-app-node` or `agent-app-python` | whether the change should instead be made in a current recommended app |
| manifest or packaging behavior | local `agent.json` | README commands, lockfile/install behavior, tests |
| repo-level example story | `README.md` | affected tool/app README, whether docs or blog briefing should change |

## Do / Don’t
- Don’t bypass `agentpm lint` for manifests.
  - Do run it in the tool or app root whenever `agent.json` changes.
- Don’t build examples that only show abstractions without proving real value.
  - Do choose examples that a user could imagine actually installing or learning from.
- Don’t overcomplicate an example to chase framework novelty.
  - Do keep the proof clear, sturdy, and legible.
- Don’t let README instructions drift from the code.
  - Do update documented setup, test, install, build, and run steps as part of the same change.
- Don’t treat old example apps as the default pattern automatically.
  - Do prefer the current recommended apps unless the task is explicitly about the legacy examples.
- Don’t add hidden environment assumptions.
    - Do document required env vars, setup steps, and expected local commands in the example README.

## Verification
## Verification
- Verify tools and agent apps when changes affect packaging, manifests, installs, or runtime behavior.
- Keep README instructions runnable and believable.
- Use the local package manager and test flow that the example already uses: `pnpm` for Node examples, `uv` for Python examples.
- When changing an example’s user-facing flow, run or trace the full documented path: setup -> install -> test/build -> run.
- If a manifest changes, run `agentpm lint` from that tool or app root.
- If an app dependency changes, check whether `agent.lock` should be updated.

## Never Do This
- Never bypass `agentpm lint` for manifest changes.
- Never leave an example in a state where it no longer runs as documented.
- Never make an example more abstract while making it less useful.
- Never change user-facing example workflows without checking whether `agentpm-api/docs` should also change.
