# cli-automation-worker

`cli-automation-worker` is a published AgentPM workflow template for bootstrapping a shell-first automation project.

It generates a local project that:

- installs the declared tools through AgentPM
- chains them with `agentpm run --input-file`
- keeps workflow logic in plain shell scripts and JSON inputs instead of SDK code
- writes a visible local markdown brief so users can prove the workflow end to end

## Generated project shape

The scaffold includes:

- `README.md`
- `.env.example`
- `scripts/run-daily-brief.sh`
- `inputs/convert.json`
- `sample-inputs/daily-notes.md`
- `outputs/`
- `tests/test_scaffold.py`

The generated root `agent.json` is synthesized by `agentpm new` from the template dependency declarations.

## Tool chain

This template currently installs:

- `@zack/document-convert`
- `@zack/summarize-text`

The generated shell script uses `document-convert` to normalize a local source file, then feeds that content into `summarize-text` with `agentpm run --input-file`.

## Variables

This template currently uses:

- `project_name`
- `workflow_label`
- `source_path`
- `output_path`

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify the scaffold locally before publish:

```bash
agentpm new . ../cli-automation-worker-test --var workflow_label="Daily Brief Worker"
```

After publish, generate a test project with:

```bash
agentpm new @zack/cli-automation-worker my-automation-worker --var workflow_label="Daily Brief Worker"
```
