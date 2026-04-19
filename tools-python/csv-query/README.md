# csv-query

Query CSV data with structured filter, sort, select, and aggregate operations.

## Why install it

CSV handling shows up constantly in ops and analyst workflows. This tool gives agents a safe, predictable query surface without embedding ad hoc dataframe code into each app.

## Inputs

- `path`: path to a local CSV file
- `csv_text`: raw CSV content passed directly to the tool
- `select`: subset of columns to keep in the output
- `filter`: filter conditions such as `eq`, `gt`, or `contains`
- `sort`: sort operations with column and optional direction
- `limit`: maximum number of rows to return
- `group_by`: columns used to group rows before aggregation
- `aggregations`: aggregate calculations such as `count`, `sum`, `avg`, `min`, and `max`

## Outputs

- `columns`: output column names
- `rows`: resulting rows after query operations
- `row_count`: number of rows returned
- `summary`: aggregate or grouping summary information

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"csv_text":"name,score\nA,2\nB,5","filter":[{"column":"score","op":"gt","value":"2"}]}' | python -u csv_query/__main__.py
```
