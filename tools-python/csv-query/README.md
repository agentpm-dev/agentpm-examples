# csv-query

Query CSV data with structured filter, sort, select, and aggregate operations.

## Why install it

CSV handling shows up constantly in ops and analyst workflows. This tool gives agents a safe, predictable query surface without embedding ad hoc dataframe code into each app.

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"csv_text":"name,score\nA,2\nB,5","filter":[{"column":"score","op":"gt","value":"2"}]}' | python -u csv_query/__main__.py
```
