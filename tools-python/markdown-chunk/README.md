# markdown-chunk

Split markdown or plain text into deterministic chunks with heading context and offsets.

## Why install it

Chunking is a repeated preprocessing step for retrieval, summarization, and memory ingestion. This tool gives you a portable chunk contract instead of one-off chunking logic per agent.

## Inputs

- `text`: markdown or plain text to chunk
- `strategy`: `heading`, `paragraph`, or `hybrid`
- `max_chars`: target maximum characters per chunk
- `overlap`: trailing character overlap carried into the next chunk when a split occurs
- `source_id`: optional source identifier copied into emitted chunks

## Outputs

- `chunks`: ordered chunk list with text, heading path, offsets, char count, and stable ID
- `metadata`: summary information including chunk count, strategy, overlap, and fallback order

## How it chunks

The tool tries to preserve structure first, then falls back only when content would exceed `max_chars`:

1. headings
2. paragraphs
3. sentences
4. fixed-size windows

When a chunk overflows, the configured `overlap` is carried into the next chunk for continuity.

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"text":"# Intro\n\nHello world","strategy":"hybrid"}' | python -u markdown_chunk/__main__.py
```
