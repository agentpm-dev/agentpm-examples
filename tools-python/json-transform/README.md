# json-transform

Apply deterministic transformation operations to JSON objects and arrays.

## Why install it

Agents constantly need to reshape API responses and intermediate data. This tool gives you a stable transformation surface instead of bespoke glue code in every workflow.

## Inputs

- `input`: input JSON value to transform
- `operations`: ordered list of transformation operations to apply

## Outputs

- `result`: final transformed JSON value
- `applied_operations`: operations that were applied successfully
- `validation_errors`: collected validation or application errors

## Supported operations

- `pick`: keep only the specified top-level keys from an object
- `rename`: rename one top-level key to another name
- `set`: assign a value at a dot-path, creating nested objects as needed
- `delete`: remove a value at a dot-path if it exists
- `flatten`: collapse a nested object into dot-path keys
- `pluck`: extract a single value from a dot-path into a new object
- `filter_array`: keep only array items whose field matches a given value

## Local development

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Example invocation

```bash
printf '%s' '{"input":{"user":{"name":"Ada","role":"admin"}},"operations":[{"op":"pluck","path":"user.name","as":"name"}]}' | python -u json_transform/__main__.py
```
