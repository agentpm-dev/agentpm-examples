from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from agentpm import load


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local", override=False)

WORKSPACE_LABEL = "zack-workspace"
SAMPLE_THREAD_PATH = ROOT / "sample-inputs/support-thread.md"
SUMMARY_SPEC = "@zack/summarize-text@0.1.8"


def collect_string_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if isinstance(value, str)
    }


def read_workspace_file() -> dict:
    return json.loads((ROOT / "agentpm.workspace.json").read_text(encoding="utf-8"))


def main() -> None:
    # This entrypoint is intentionally small. The goal of this template is to
    # teach the generated workspace shape, not to pretend AgentPM already owns
    # recursive multi-agent orchestration semantics for these manifests.
    print(f"\n{WORKSPACE_LABEL}")
    print("Generated multi-agent workspace example")
    print(f"Sample thread: {SAMPLE_THREAD_PATH}")

    workspace = read_workspace_file()
    print("\nWorkspace manifests:")
    for manifest_path in workspace.get("manifests", []):
        print(f"- {manifest_path}")

    print("\nPublished agent roots:")
    for agent_root in workspace.get("package_roots", {}).get("agents", []):
        print(f"- {agent_root['name']}@{agent_root['version']}")

    # The root app uses its own direct tool dependency here. That keeps the
    # runtime example honest: the workspace can contain multiple local and
    # published agent roles, while normal application code still decides what to
    # do with them.
    if not os.getenv("OPENAI_API_KEY"):
        print("\nNo OPENAI_API_KEY found. Skipping the illustrative summary step.")
        return

    summary_tool = load(SUMMARY_SPEC, with_meta=True, env=collect_string_env())
    thread_text = SAMPLE_THREAD_PATH.read_text(encoding="utf-8")
    result = summary_tool["func"]({"text": thread_text, "max_words": 120})

    print("\nIllustrative summary from the root workspace tool set:\n")
    print(result.get("summary", result))
    print("")


if __name__ == "__main__":
    main()
