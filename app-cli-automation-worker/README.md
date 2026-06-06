# app-cli-automation-worker

zack-worker is a shell-first automation example generated from the published `@zack/cli-automation-worker` workflow template.

It demonstrates a non-SDK AgentPM workflow:

- `agentpm run --input-file` drives each tool invocation
- shell scripts orchestrate the steps
- local files provide inputs and outputs
- the result is a markdown brief at `outputs/daily-brief.md`

## What this project does

The generated script:

1. reads a local source document from `sample-inputs/daily-notes.md`
2. runs `@zack/document-convert` to normalize it into markdown/text content
3. builds a summary payload in `.tmp/summary-input.json`
4. runs `@zack/summarize-text`
5. writes a final markdown brief to `outputs/daily-brief.md`

## Setup

```bash
cp .env.example .env.local
agentpm install
```

Set:

- `OPENAI_API_KEY`

## Run

```bash
bash scripts/run-daily-brief.sh
```

## Inputs and outputs

- source document:
  - `sample-inputs/daily-notes.md`
- runtime temp files:
  - `.tmp/convert-runtime.json`
  - `.tmp/converted.json`
  - `.tmp/summary-input.json`
  - `.tmp/summary.json`
- final report:
  - `outputs/daily-brief.md`

## Why this example matters

This scaffold is intentionally aimed at users who think in:

- shell scripts
- cron jobs
- scheduled CI workflows
- small operational automations

The first run is entirely local and file-based. Once you are happy with the script, you can expand it into:

- cron
- launchd or systemd timers
- GitHub Actions
- larger pipelines that replace the sample input file with a real upstream source

## Review the sample source

The scaffold includes a sample local source document at:

```text
sample-inputs/daily-notes.md
```

You can replace that file with your own markdown, text, JSON, HTML, or CSV input once you want to adapt the workflow.

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
