# markdown-chunk

Split markdown or plain text into deterministic chunks with heading context and offsets.

## Why install it

Chunking is a repeated preprocessing step for retrieval, summarization, and memory ingestion. This tool gives you a portable chunk contract instead of one-off chunking logic per agent.

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"text":"# Intro\n\nHello world","strategy":"hybrid"}' | python -u markdown_chunk/__main__.py
```
