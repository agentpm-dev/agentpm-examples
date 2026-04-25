# document-convert

Convert local documents into normalized markdown or plain text with lightweight metadata.

## Why install it

Knowledge workflows need a common representation for mixed source files. This tool gives an agent a simple document normalization primitive for text, markdown, HTML, JSON, and CSV inputs.

## Inputs

- `path`: path to the local document to convert
- `to_format`: `markdown` or `text`
- `extract_metadata`: whether to include file metadata such as size and line count

## Outputs

- `path`: original file path
- `media_type`: detected media type for the input
- `content`: converted document body
- `metadata`: file and conversion metadata

## Local development

The source code for this tool can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/tools-python/document-convert)

Test:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
python -u document_convert/__main__.py < input.json
```

With input.json containing:

```json
 {
    "path": "fixtures/sample.html",
    "to_format": "markdown"
  }
```
