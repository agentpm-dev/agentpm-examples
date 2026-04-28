# `agentpm-examples` Repo Review Guide

This repo should prove that AgentPM is worth using. Reviews should prioritize whether examples demonstrate real value, whether manifests and READMEs match actual behavior, and whether the current recommended examples remain clear and runnable.

## Review Focus
- whether examples demonstrate real value
- whether publish, install, and use flows still make sense
- manifest and lockfile correctness
- missing or insufficient tests
- misleading or stale docs
- mismatch between `agent.json`, `agent.lock`, READMEs, and actual behavior
- whether current recommended agent apps still clearly demonstrate distinct orchestration styles

## Review Principles
- Review examples as product proof, not just as code samples.
- Treat READMEs and manifests as part of the contract of the example.
- Prefer findings about realism, clarity, verification, and contract drift over style-only critique.
- Be especially skeptical of changes that make an example more abstract while making it less obviously useful.

## Blocking Issues
- examples that no longer run as documented
- manifest problems or unlinted manifest changes
- broken publish, install, or use flows
- stale or misleading README instructions
- examples that misrepresent what AgentPM actually supports
- current recommended apps that no longer clearly show their intended orchestration style
- missing verification after packaging or runtime behavior changes

## Specific Review Checks
- If `agent.json` changed, verify that `agentpm lint` was rerun and that the README and tests still match the new manifest behavior.
- If an app’s `agent.json` changed, check whether `agent.lock` or documented install flow should also have changed.
- If a tool changed, review code, tests, README, and manifest together rather than in isolation.
- If an agent app changed, verify that its orchestration style is still legible and still distinct from the other current recommended apps.
- If README commands changed, treat them as executable claims and check whether they still line up with the package manager and runtime configuration actually used by the example.
- If a change materially affects what users learn about AgentPM, verify that `agentpm-api/docs` was updated when appropriate.
- If a finished spec seems blog-worthy, verify whether the spec output left behind useful material for `blog-brief.md`.

## Decision Guide

| If the review touches... | Focus first on... | Also inspect |
|---|---|---|
| a Node tool | manifest/runtime realism | README, tests, package/build config |
| a Python tool | manifest/runtime realism | README, tests, `pyproject.toml` |
| a current recommended agent app | clarity of orchestration pattern | `agent.json`, `agent.lock`, README, terminal UX |
| a legacy agent app | whether the change belongs there at all | whether a current recommended app should be the real target |
| manifest or packaging behavior | contract correctness | README instructions, tests, install flow |
| repo-level example positioning | realism and usefulness | top-level README, affected tool/app docs |

## Do / Don’t
- Don’t review manifests separately from the example that consumes them.
  Do review `agent.json`, code, tests, README, and lock/install behavior together.
- Don’t accept examples that only sound impressive.
  Do ask whether the example actually proves reusable value or a believable learning path.
- Don’t treat legacy examples as the default quality bar.
  Do hold the current recommended agent apps to the clearest standard.
- Don’t ignore stale README commands.
  Do flag them as contract problems, not minor documentation nits.

## Low-Value Review Noise
- avoid style-only critique unless it harms clarity or educational value
- avoid abstract architecture commentary unless it affects the repo’s proof value
- avoid nitpicking simplicity when the example is intentionally narrow and sturdy
