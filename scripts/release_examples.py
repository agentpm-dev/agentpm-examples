"""Select explicit package tags and check installed examples without SDK execution."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "summarize-text": "tools-python/summarize-text",
    "devwork-copilot": "agent-packages/devwork-python",
    "native-release-check": "publishing/native-release-check",
}


def select(tag, namespace):
    name, separator, version = tag.partition("/v")
    if name not in PACKAGES or not separator or not version:
        raise ValueError("Use an exact supported package/v<version> tag")
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", namespace):
        raise ValueError("Set AGENTPM_NAMESPACE to a namespace handle you own")
    directory = PACKAGES[name]
    manifest = json.loads((ROOT / directory / "agent.json").read_text())
    if manifest["name"] != name or manifest["version"] != version:
        raise ValueError(
            "Release tag does not match the selected agent.json name/version"
        )
    return {
        "name": name,
        "version": version,
        "package_dir": directory,
        "ref": f"@{namespace}/{name}@{version}",
    }


def verify(name, ref, consumer):
    lock = json.loads((consumer / "agent.lock").read_text())
    manifest = json.loads((ROOT / PACKAGES[name] / "agent.json").read_text())
    expected = ref.rsplit("@", 1)[0]
    entries = [
        p
        for p in lock["packages"].values()
        if p["name"] == expected and p["version"] == manifest["version"]
    ]
    if len(entries) != 1:
        raise ValueError("Exact published package missing from consumer lock")
    if name == "devwork-copilot":
        for tool in manifest["tools"]:
            if not any(
                p["name"] == tool["name"] and p["version"] == tool["version"]
                for p in lock["packages"].values()
            ):
                raise ValueError(
                    "Agent dependency version differs from the authored manifest"
                )
        print(
            "Verified exact Agent and declared Tool dependencies; no SDK/model run required."
        )
        return
    data = (
        {"value": 3}
        if name == "native-release-check"
        else {
            "text": "The maintainer reproduced the bug and requested a regression test.",
            "max_words": 50,
        }
    )
    # Separate model credential: only the summarizer's explicit verification calls a provider.
    if name == "summarize-text" and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "Successful summarizer verification requires the separate OPENAI_API_KEY secret"
        )
    result = subprocess.run(
        ["agentpm", "run", ref, "--machine", "--input", json.dumps(data)],
        cwd=consumer,
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(result.stdout)
    if value["status"] != "success":
        raise ValueError("Tool runner did not succeed")
    output = value["output"]
    if name == "native-release-check":
        if output != {"value": 4}:
            raise ValueError("Installed native helper returned the wrong result")
    elif output.get("ok") is not True or not output.get("summary"):
        raise ValueError("Summarizer returned an application error or empty summary")
    print("Verified exact installed Tool execution.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("select")
    selection.add_argument("tag")
    selection.add_argument("namespace")
    check = sub.add_parser("verify")
    check.add_argument("name", choices=PACKAGES)
    check.add_argument("ref")
    check.add_argument("consumer", type=Path)
    args = parser.parse_args()
    if args.command == "select":
        values = select(args.tag, args.namespace)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("".join(f"{key}={value}\n" for key, value in values.items()))
    else:
        verify(args.name, args.ref, args.consumer)


if __name__ == "__main__":
    main()
