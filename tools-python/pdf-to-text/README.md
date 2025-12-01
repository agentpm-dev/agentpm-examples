## pdf-to-text

### What it does
Extract text from PDFs, either from a URL or base64-encoded PDF data.

### AgentPM manifest
See `agent.json` in this folder. It declares:
- `"kind": "tool"`, `"runtime": { "type": "python", "version": "3.11" }`
- `"entrypoint": { "command": "python", "args": ["-u", "pdf_to_text/__main__.py"] }`
- JSON Schema for **inputs** and **outputs**

### Quirks

> Entrypoint reads JSON from **stdin** and prints a single JSON object to **stdout**.

### Setup & run
```bash
# install deps (uv)
uv sync --directory tools-python/pdf-to-text

# run
uv run --directory tools-python/pdf-to-text \
python -m pdf_to_text <<'JSON'
{"pdf_url": "https://ontheline.trincoll.edu/images/bookdown/sample-local-pdf.pdf"}                     
JSON

```

### Vendor Dependencies before publishing
```bash
uv pip install \
  --target tools-python/pdf-to-text/pdf_to_text/_vendor \
  "pypdf>=5.0.0" \
  "httpx>=0.27.0"
```
