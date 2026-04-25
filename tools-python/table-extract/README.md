# table-extract

Extract structured tables from HTML or CSV sources into normalized rows and columns.

## Why install it

Research workflows frequently encounter useful data trapped in tables. This tool gives agents a portable table extraction primitive without requiring a full scraping stack.

## Inputs

- `source_type`: `html`, `csv`, or `auto`
- `path`: optional local file path for the source
- `html_text`: optional raw HTML content
- `csv_text`: optional raw CSV content
- `table_index`: zero-based table index for HTML extraction
- `header_row`: whether the first row should be treated as the header

## Outputs

- `tables`: extracted tables with columns and rows
- `detected_count`: number of tables detected in the source
- `warnings`: extraction warnings
- `metadata`: summary metadata about the extraction

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
python -u table_extract/__main__.py < input.json
```

With input.json containing:

```json
{
  "html_text": "<table><tr><th>Name</th></tr><tr><td>Ada</td></tr></table>",
  "source_type": "html"
}
```
