#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_ROOT = WORKSPACE_ROOT.parent
CORPUS_ROOT = PROVIDERS_ROOT.parent / "m13-reference-corpus"
CORPUS_INSTALL_ROOT = (
    WORKSPACE_ROOT
    / ".agentpm"
    / "knowledge"
    / "zack"
    / "m13-reference-corpus"
    / "0.1.0"
)
LOOP_SOURCE_ROOT = WORKSPACE_ROOT / "loops" / "m13-reference-loop"
LOOP_INSTALL_ROOT = (
    WORKSPACE_ROOT / ".agentpm" / "loops" / "zack" / "m13-reference-loop" / "0.1.0"
)


def require_file(path: Path, message: str) -> None:
    if not path.is_file():
        raise SystemExit(f"{message}: {path}")


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__", ".DS_Store")
    shutil.copytree(source, destination, ignore=ignore)


def main() -> None:
    require_file(CORPUS_ROOT / "agent.json", "M13 corpus manifest not found")
    require_file(
        CORPUS_ROOT / "knowledge" / "embeddings" / "default.f32",
        "M13 corpus embeddings are missing; run scripts/embed_openai.py from m13-reference-corpus first",
    )
    require_file(
        CORPUS_ROOT / "knowledge" / "indexes" / "default" / "metadata.json",
        "M13 corpus index metadata is missing; run agentpm knowledge build from m13-reference-corpus first",
    )
    require_file(
        LOOP_SOURCE_ROOT / "agent.json", "M13 reference loop manifest not found"
    )

    copy_tree(CORPUS_ROOT, CORPUS_INSTALL_ROOT)
    copy_tree(LOOP_SOURCE_ROOT, LOOP_INSTALL_ROOT)

    lock = {
        "generated": "2026-09-02T00:00:00Z",
        "lockfile_version": 3,
        "packages": {
            "knowledge:@zack/m13-reference-corpus@0.1.0": {
                "integrity": "local-m13-reference-corpus",
                "kind": "knowledge",
                "name": "@zack/m13-reference-corpus",
                "version": "0.1.0",
            },
            "loop:@zack/m13-reference-loop@0.1.0": {
                "integrity": "local-m13-reference-loop",
                "kind": "loop",
                "name": "@zack/m13-reference-loop",
                "version": "0.1.0",
            },
        },
        "roots": {
            "local:agent": {
                "knowledge": ["knowledge:@zack/m13-reference-corpus@0.1.0"],
                "loop": "loop:@zack/m13-reference-loop@0.1.0",
                "name": "m13-reference-harness-agent",
                "version": "0.1.0",
            }
        },
    }
    (WORKSPACE_ROOT / "agent.lock").write_text(
        json.dumps(lock, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared Harness workspace: {WORKSPACE_ROOT}")
    print(f"Installed corpus: {CORPUS_INSTALL_ROOT}")
    print(f"Installed loop: {LOOP_INSTALL_ROOT}")


if __name__ == "__main__":
    main()
