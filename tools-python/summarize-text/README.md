# summarize-text

Summarize text to a target word budget using OpenAI's `gpt-4o-mini`. The Tool
reads one JSON object from stdin and writes one JSON object to stdout. Its
existing `ok`/`summary` and `ok`/`error` interface is unchanged.

Version **0.1.9** declares `openai>=1.51.0,<2` in `agent.json`, keeping the OpenAI 1.x
interface. The prepared `agent.lock` records the complete exact dependency set,
including native dependencies such as `pydantic-core` and `jiter`. Consumers
need AgentPM CLI **0.1.37 or newer** and Python **3.11 or newer**.
AgentPM runs the `summarize_text` Python module from the Tool's root directory.

## Develop and Test

From this directory:

```bash
uv sync
uv run python -m unittest discover -s tests -p 'test_*.py'
```

Tests use a local HTTP mock transport with the real OpenAI client and import
the native Pydantic extension. They make no network requests or paid model calls.
The developer's `.venv` is separate from consumers' AgentPM-managed environments.
`python-dotenv[cli]` is a development convenience, not a Tool runtime dependency.

For a real model call, put `OPENAI_API_KEY` in your ignored `.env.local`:

```bash
uv run python -m dotenv -f .env.local run -- python -m summarize_text <<'JSON'
{"text":"Alan Turing was a computer scientist","max_words":60}
JSON
```

This makes a paid API request. Successful output has the form
`{"ok":true,"summary":"..."}`. A missing API key returns a structured
`INPUT_MISSING_API_KEY` value error with exit code zero, as before.

## Prepare and Publish

Keep `pyproject.toml` and `agent.json` runtime requirements in agreement. Do not
vendor dependencies into `summarize_text/_vendor`; remove any old ignored copy
from your local working directory before packaging this version. The Tool now
imports dependencies from the interpreter's environment.

Use AgentPM CLI **0.1.37 or newer**. The checked-in `agent.lock` is already
prepared for this version; package it without refreshing the reviewed resolution:

```bash
agentpm lint --strict
agentpm publish --dry-run
git diff -- agent.json agent.lock
# Review the dependency state, then publish to a namespace you own.
agentpm publish --namespace your-namespace
```

Review and commit the portable `agent.lock` with the source; no local environment
paths belong in it. Publication
reuses this recorded resolution instead of resolving again. Use
`agentpm publish --dry-run --refresh-python` only when intentionally updating the
dependency state, then review and commit the resulting lock before publishing.

## Consumer Use

With a suitable Python selected, use the namespace where the Tool was published
(the commands below use `@zack`):

```bash
agentpm install @zack/summarize-text@0.1.9
export OPENAI_API_KEY='your-key'
agentpm run @zack/summarize-text@0.1.9 --input '{"text":"Alan Turing was a computer scientist","max_words":60}'
```

If `python` is absent or too old, set `AGENTPM_PYTHON` to an absolute Python 3.11+
executable before install and run. AgentPM installs exact hash-verified wheels
into `.agentpm/runtimes/python/` and runs the Tool with that Python automatically.
No consumer `uv sync`, manual pip install or global OpenAI package is required.
Harness Tool calls use the same environment through `agentpm run --machine`.
