from __future__ import annotations

import json
import os
from typing import Any

from agentpm import load, load_agent, load_skill
from langchain_core.tools import StructuredTool
from pydantic import Field, create_model
from pydantic.fields import PydanticUndefined

JsonValue = Any
AGENT_SPEC = "@zack/devwork-copilot@0.1.1"


def collect_string_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if isinstance(value, str)
    }


def _spec_from_entry(entry: dict[str, Any]) -> str:
    return f'{entry["name"]}@{entry["version"]}'


def _schema_type_to_python(prop: dict[str, Any]) -> tuple[Any, Field]:
    schema_type = prop.get("type")
    description = prop.get("description", "")
    default = ... if "default" not in prop else prop.get("default")

    if "enum" in prop and isinstance(prop["enum"], list) and prop["enum"]:
        annotation = str
    elif schema_type == "string":
        annotation = str
    elif schema_type == "integer":
        annotation = int
    elif schema_type == "number":
        annotation = float
    elif schema_type == "boolean":
        annotation = bool
    elif schema_type == "array":
        annotation = list
    elif schema_type == "object":
        annotation = dict
    else:
        annotation = Any

    return annotation, Field(default=default, description=description)


def build_args_model(tool_name: str, inputs_schema: dict[str, Any] | None) -> type:
    if not isinstance(inputs_schema, dict):
        return create_model(f"{tool_name.title().replace('-', '')}Args")

    properties = inputs_schema.get("properties") or {}
    required = set(inputs_schema.get("required") or [])

    fields: dict[str, tuple[Any, Field]] = {}
    for key, prop in properties.items():
        if not isinstance(prop, dict):
            fields[key] = (Any | None, Field(default=None, description=""))
            continue

        annotation, field = _schema_type_to_python(prop)
        if key not in required:
            annotation = annotation | None
            default = None if field.default is PydanticUndefined else field.default
            field = Field(default=default, description=field.description)
        fields[key] = (annotation, field)

    return create_model(f"{tool_name.title().replace('-', '')}Args", **fields)


def _stringify_result(value: JsonValue, max_chars: int = 8000) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False)

    return text if len(text) <= max_chars else json.dumps(
        {"truncated": True, "result_preview": text[:max_chars]}, ensure_ascii=False
    )


def _rich_description(meta: dict[str, Any]) -> str:
    description = meta.get("description") or f'AgentPM tool {meta.get("name", "tool")}'
    inputs = meta.get("inputs")
    outputs = meta.get("outputs")
    if inputs is not None:
        description += f" Inputs: {json.dumps(inputs, ensure_ascii=False)}."
    if outputs is not None:
        description += f" Outputs: {json.dumps(outputs, ensure_ascii=False)}."
    return description


def load_langchain_tools() -> tuple[dict[str, Any], list[dict[str, Any]], list[StructuredTool], list[dict[str, Any]]]:
    loaded_agent = load_agent(AGENT_SPEC)
    loaded_skills: list[dict[str, Any]] = []
    loaded_tools: list[StructuredTool] = []
    metas: list[dict[str, Any]] = []
    env = collect_string_env()
    seen_specs: set[str] = set()

    for entry in loaded_agent.get("resolvedTools", []):
        spec = _spec_from_entry(entry)
        if spec in seen_specs:
            continue
        seen_specs.add(spec)
        loaded = load(spec, with_meta=True, env=env)
        func = loaded["func"]
        meta = loaded["meta"]
        tool_name = meta["name"]
        args_model = build_args_model(tool_name, meta.get("inputs"))

        def _invoke_tool(_func=func, _tool_name=tool_name, **kwargs: Any) -> str:
            payload = {key: value for key, value in kwargs.items() if value is not None}
            try:
                result = _func(payload)
            except Exception as exc:
                print("[tool wrapper error]")
                print(f"{_tool_name}: {exc}")
                raise

            print("[tool result]")
            print(_stringify_result(result, 1800))
            return _stringify_result(result)

        tool = StructuredTool.from_function(
            func=_invoke_tool,
            name=tool_name,
            description=_rich_description(meta),
            args_schema=args_model,
        )
        loaded_tools.append(tool)
        metas.append(meta)

    for skill_entry in loaded_agent.get("resolvedSkills", []):
        loaded_skill = load_skill(_spec_from_entry(skill_entry))
        loaded_skills.append(loaded_skill)
        for entry in loaded_skill.get("resolvedTools", []):
            spec = _spec_from_entry(entry)
            if spec in seen_specs:
                continue
            seen_specs.add(spec)
            loaded = load(spec, with_meta=True, env=env)
            func = loaded["func"]
            meta = loaded["meta"]
            tool_name = meta["name"]
            args_model = build_args_model(tool_name, meta.get("inputs"))

            def _invoke_tool(_func=func, _tool_name=tool_name, **kwargs: Any) -> str:
                payload = {key: value for key, value in kwargs.items() if value is not None}
                try:
                    result = _func(payload)
                except Exception as exc:
                    print("[tool wrapper error]")
                    print(f"{_tool_name}: {exc}")
                    raise

                print("[tool result]")
                print(_stringify_result(result, 1800))
                return _stringify_result(result)

            tool = StructuredTool.from_function(
                func=_invoke_tool,
                name=tool_name,
                description=_rich_description(meta),
                args_schema=args_model,
            )
            loaded_tools.append(tool)
            metas.append(meta)

    return loaded_agent, loaded_skills, loaded_tools, metas
