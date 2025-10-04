## summarize-text

### What it does
Summarizes input text to a target length using OpenAI.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "python", "version": "3.11" }`
- `"entrypoint": { "command": "python", "args": ["-u", "summarize_text/__main__.py"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks
- Requires `OPENAI_API_KEY`.

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run
```bash
# install deps (uv)
uv sync --directory tools-python/summarize-text

uv add --directory tools-python/summarize-text python-dotenv
uv add --directory tools-python/summarize-text "python-dotenv[cli]"

# run with env
uv run --directory tools-python/summarize-text \
python -m dotenv -f .env.local run -- \
python -m summarize_text <<'JSON'
{"text":"Alan Turing was a computer scientist","max_words":60}
JSON
```

### Vendor Dependencies before publishing
```bash
uv pip install --target tools-python/summarize-text/summarize_text/_vendor "openai>=1.51.0"
```