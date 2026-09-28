# {{ project_name }}

{{ workspace_label }} is a minimal AgentPM Harness workspace.

It installs one published Agent package, `@zack/devwork-copilot@0.1.6`, then lets the AgentPM reference Harness run that Agent from the terminal.

## What this workspace shows

- `agentpm new` creates a normal consumer-owned workspace.
- `agentpm.harness.json` realizes the installed Agent for local runtime execution.
- `agentpm harness` opens the interactive TUI.
- `agentpm harness --headless` runs the same Agent as a one-shot command and writes a report.
- `.agentpm-state/` is runtime state. It is safe to inspect, but it is not part of the template.

## Package graph

The Template depends directly on:

- `@zack/devwork-copilot@0.1.6`

That Agent package brings in the broader package graph:

- Loop: `@zack/devwork-triage-loop@0.1.0`
- Skill: `@zack/issue-triage-playbook@0.1.0`
- Tool through the Skill: `@zack/github-issues@0.1.1`
- Knowledge: `@zack/devwork-maintainer-guide@0.1.0`
- Memory: `@zack/devwork-maintainer-state@0.1.0`
- Profile: `@zack/devwork-maintainer-style@0.1.0`

The Agent intentionally does not include the old `@zack/summarize-text` dependency. That Tool is architecture-sensitive and is not needed for this Harness starter.

## First run

Create a local env file:

```bash
cp .env.local.example .env.local
```

Set `OPENAI_API_KEY` in `.env.local`, then export the file into your current shell before running Harness:

```bash
set -a
source .env.local
set +a
```

Check readiness:

```bash
agentpm harness --json
```

Open the TUI:

```bash
agentpm harness
```

Send a prompt such as:

```text
Review this generated workspace and summarize what the installed Agent can do.
```

## Headless run

For scripts, CI, or non-interactive terminals, use `--headless` instead of the TUI:

```bash
mkdir -p reports
agentpm harness \
  --headless \
  --input "Review this generated workspace and summarize what the installed Agent can do." \
  --report reports/first-run.json
```

Inspect the report path and trace path:

```bash
python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("reports/first-run.json").read_text())
print("terminal_status:", report.get("terminal_status"))
print("trace_path:", report.get("trace_path"))
PY
```

## Local Ollama option

If you have Ollama running locally and have pulled `{{ ollama_model }}`, use the included Ollama config:

```bash
ollama pull {{ ollama_model }}
agentpm harness --config agentpm.ollama.harness.json
```

For a one-shot run:

```bash
mkdir -p reports
agentpm harness \
  --config agentpm.ollama.harness.json \
  --headless \
  --input "Review this generated workspace and summarize what the installed Agent can do." \
  --report reports/ollama-first-run.json
```

## If it does not run

Start with the preflight report:

```bash
agentpm harness --json
```

Look at:

- `readiness`
- `diagnostics`
- configured Agent, Loop, model, scope, Knowledge, Memory, and Tool entries

Common blockers for this template:

- `OPENAI_API_KEY` is missing for the default OpenAI config.
- Ollama is not running or `{{ ollama_model }}` has not been pulled for `agentpm.ollama.harness.json`.
- `user` or `repository` scope was removed from `agentpm.harness.json`.
- The cleaned `@zack/devwork-copilot@0.1.6` package has not been published yet.
- A prompt asks for live GitHub issue data without `GITHUB_TOKEN`.

## Common next additions

- Change the model in `agentpm.harness.json`.
- Use `agentpm.ollama.harness.json` for local model testing.
- Raise `trace.level` to `verbose` when debugging.
- Change `trace.content` from `redacted` to `full` only for local debugging or controlled environments. Secret-keyed fields are still redacted; credentials are never a phase handoff mechanism.
- Add a second AgentPM Tool to the Agent package, publish it, then install the updated Agent.
- Add an external MCP import once you want Harness to augment Agent-authored capabilities.
- Move from the TUI to `--headless` for scripts or to `--machine` when an SDK host controls the session.

## Cross-platform notes

The TUI requires a real interactive terminal. CI jobs and non-interactive shells should use `--headless` or SDK `--machine` control.

The commands above use POSIX shell syntax. In PowerShell, set environment variables with:

```powershell
$env:OPENAI_API_KEY = "..."
$env:GITHUB_TOKEN = "..."
```

## Files to know

- `agentpm.harness.json`: default OpenAI Harness runtime config.
- `agentpm.ollama.harness.json`: local Ollama Harness runtime config.
- `maintainer-context.md`: consumer context file referenced by the installed Agent bindings.
- `reports/`: local report output location for headless runs.
- `.agentpm-state/`: Harness runtime state; ignored by git.
