# json-transform

Apply deterministic transformation operations to JSON objects and arrays.

## Why install it

Agents constantly need to reshape API responses and intermediate data. This tool gives you a stable transformation surface instead of bespoke glue code in every workflow.

## Supported operations

- `pick`
- `rename`
- `set`
- `delete`
- `flatten`
- `pluck`
- `filter_array`

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"input":{"user":{"name":"Ada","role":"admin"}},"operations":[{"op":"pluck","path":"user.name","as":"name"}]}' | python -u json_transform/__main__.py
```
