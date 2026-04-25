from __future__ import annotations

import json
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler


def _truncate(value: Any, max_chars: int = 1200) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, indent=2)
        except TypeError:
            text = str(value)
    return text if len(text) <= max_chars else f"{text[:max_chars]}\n...<truncated>"


class OpsVerboseHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        name = serialized.get("name", "tool")
        print(f"\n[tool selected] {name}")
        print("[tool args]")
        print(_truncate(input_str, 1200))

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        print("[tool return to model]")
        print(_truncate(output, 1800))

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        print("[tool error]")
        print(_truncate(str(error), 1800))
