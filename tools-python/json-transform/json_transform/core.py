from __future__ import annotations

from copy import deepcopy


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _get_path(value, path: str):
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _set_path(value, path: str, new_value):
    current = value
    parts = path.split(".")
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = new_value


def _delete_path(value, path: str):
    current = value
    parts = path.split(".")
    for part in parts[:-1]:
        current = current.get(part)
        if not isinstance(current, dict):
            return
    if isinstance(current, dict):
        current.pop(parts[-1], None)


def _flatten_dict(value: dict, prefix: str = "") -> dict:
    out = {}
    for key, item in value.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            out.update(_flatten_dict(item, full_key))
        else:
            out[full_key] = item
    return out


def transform_json(*, input, operations: list[dict]) -> dict:
    result = deepcopy(input)
    applied: list[str] = []
    errors: list[str] = []

    for operation in operations:
        op = operation.get("op")
        try:
            if op == "pick":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "pick requires object input")
                keys = operation.get("keys", [])
                result = {key: result[key] for key in keys if key in result}
            elif op == "rename":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "rename requires object input")
                from_key = operation.get("from")
                to_key = operation.get("to")
                if from_key in result:
                    result[to_key] = result.pop(from_key)
            elif op == "set":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "set requires object input")
                _set_path(result, operation["path"], operation.get("value"))
            elif op == "delete":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "delete requires object input")
                _delete_path(result, operation["path"])
            elif op == "flatten":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "flatten requires object input")
                result = _flatten_dict(result)
            elif op == "pluck":
                if not isinstance(result, dict):
                    raise ToolError("INPUT_INVALID", "pluck requires object input")
                alias = operation.get("as") or operation["path"].split(".")[-1]
                result = {alias: _get_path(result, operation["path"])}
            elif op == "filter_array":
                if not isinstance(result, list):
                    raise ToolError("INPUT_INVALID", "filter_array requires array input")
                path = operation.get("path")
                equals = operation.get("equals")
                result = [item for item in result if isinstance(item, dict) and _get_path(item, path) == equals]
            else:
                raise ToolError("INPUT_INVALID", f"Unsupported operation: {op}")
            applied.append(op)
        except ToolError as exc:
            errors.append(str(exc))
    return {
        "result": result,
        "applied_operations": applied,
        "validation_errors": errors,
    }
