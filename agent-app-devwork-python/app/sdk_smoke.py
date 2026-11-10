"""Load the installed Agent and call its Python Tool without a model request."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from agentpm import load, load_agent, load_skill


def main() -> None:
    if len(sys.argv) > 1:
        os.chdir(Path(sys.argv[1]).resolve())
    agent = load_agent("@zack/devwork-copilot@0.1.8")
    refs = list(agent["resolvedTools"])
    for entry in agent["resolvedSkills"]:
        skill = load_skill(f"{entry['name']}@{entry['version']}")
        refs.extend(skill["resolvedTools"])
    summarize = next(ref for ref in refs if ref["name"] == "@zack/summarize-text")
    spec = f"{summarize['name']}@{summarize['version']}"
    invoke = load(spec, env={"OPENAI_API_KEY": ""})
    result = invoke({"text": "SDK dependency smoke", "max_words": 50})
    assert isinstance(result, dict) and result.get("ok") is False, result
    error = result.get("error")
    assert (
        isinstance(error, dict) and error.get("code") == "INPUT_MISSING_API_KEY"
    ), result
    print(
        json.dumps(
            {"agent": agent["manifest"]["version"], "tool": spec, "output": result}
        )
    )


if __name__ == "__main__":
    main()
