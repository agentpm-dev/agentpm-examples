# validate-order

Validate an order and return its total. The code imports Pydantic, which uses
the native `pydantic-core` wheel. This demonstrates the full Python dependency
flow: author development, portable resolution, installation and execution.
It uses no API key, LLM or external service at runtime.

This example requires an AgentPM CLI containing Milestone 11C for managed
consumer environments. It is source code for a publishable Tool, not a claim
that `validate-order` is already published in any particular namespace.

## Develop the Tool

From this directory, using Python 3.11 or newer:

```bash
uv sync
uv run python -m unittest discover -s tests -p 'test_*.py'
printf '%s\n' '{"quantity":2,"unit_price":4.5}' | uv run python tool.py
```

Expected: tests pass and the last command prints `{"total": 9.0}`. Pydantic
validates the actual input; the Tool is not merely declaring an unused package.
The developer's `.venv` is separate from consumers' AgentPM-managed environments.
Keep `pyproject.toml` and `agent.json` dependency declarations in agreement.

## Prepare and Publish

Use your rebuilt CLI, matching local schema, dev Registry and a namespace you
own when testing unreleased 11C code. The shorthand commands below assume those
are already selected; the public schema/released CLI may lag your working tree.
For working-tree checks, add `--schema /absolute/path/to/agentpm/schemas/agentpm.manifest.schema.json`
to lint/publish, and put `--base-url http://127.0.0.1:5000` before the subcommand
when using the local Registry. Use the rebuilt executable's path in place of
`agentpm` until that code is released.

```bash
agentpm lint --strict
agentpm publish --dry-run --refresh-python
git diff -- agent.lock
# Review and commit agent.json and agent.lock before shared/CI publication.
agentpm publish --namespace your-namespace
```

Supply normal publish credentials. Preparation creates `local:tool` Python
state in `agent.lock`; the published archive carries Tool-only
`agentpm-python.json`. Consumers use those exact recorded versions and hashes.
The CLI validates lock contents/freshness, rather than enforcing a Git commit.

## Use the Published Tool

In a different project with a suitable Python installed, replace the namespace
below with the one where you actually published version 0.1.0:

```bash
export ORDER_TOOL='@your-namespace/validate-order@0.1.0'
agentpm install "$ORDER_TOOL"
agentpm run "$ORDER_TOOL" --input '{"quantity":2,"unit_price":4.5}'
```

If `python` is not on PATH or points at an older interpreter, set
`AGENTPM_PYTHON` to the absolute path of a suitable Python before both commands.

Expected: `{"total":9.0}`. Install prepares an isolated environment under
`.agentpm/runtimes/python/`. Run selects its Python automatically. The consumer
does not need to run `uv sync`, install Pydantic globally or activate a venv.
If the selected Python changes, follow the reinstall guidance before running.

To use it through Harness, add the same package reference to an Agent's `tools`
list and run `agentpm install` in that Agent's workspace. In your already
configured Harness/provider setup, ask the Agent to validate two units at 4.5
each. Its Tool call uses `agentpm run --machine` and the same managed environment.
Harness preflight reports an unavailable environment with reinstall guidance.
The example does not add a new Harness provider or require a paid model for
the direct CLI checks.
