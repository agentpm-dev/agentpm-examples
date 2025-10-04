## sentiment-analysis

### What it does
Simple sentiment analysis over text (e.g., rule-based / lexicon) using VADER.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "python", "version": "3.11" }`
- `"entrypoint": { "command": "python", "args": ["-u", "sentiment_analysis/__main__.py"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run
```bash
# install deps (uv)
uv sync --directory tools-python/sentiment-analysis

# run
uv run --directory tools-python/sentiment-analysis \
python -m sentiment_analysis <<'JSON'
{"text":"Alan Turing is one of history's most influential computer scientists"}
JSON
```

### Vendor Dependencies before publishing
```bash
uv pip install --target tools-python/sentiment-analysis/sentiment_analysis/_vendor "vaderSentiment>=3.3.2"
```
