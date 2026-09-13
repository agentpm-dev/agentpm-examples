#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_ROOT = WORKSPACE_ROOT.parent
MEMORY_ROOT = PROVIDERS_ROOT.parent / "m16-reference-memory"
MEMORY_INSTALL_ROOT = (
    WORKSPACE_ROOT / ".agentpm" / "memory" / "zack" / "m16-reference-memory" / "0.1.0"
)
LOOP_SOURCE_ROOT = WORKSPACE_ROOT / "loops" / "m16-reference-loop"
LOOP_INSTALL_ROOT = (
    WORKSPACE_ROOT / ".agentpm" / "loops" / "zack" / "m16-reference-loop" / "0.1.0"
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
    require_file(MEMORY_ROOT / "agent.json", "M16 Memory manifest not found")
    require_file(LOOP_SOURCE_ROOT / "agent.json", "M16 reference loop manifest not found")

    copy_tree(MEMORY_ROOT, MEMORY_INSTALL_ROOT)
    copy_tree(LOOP_SOURCE_ROOT, LOOP_INSTALL_ROOT)

    lock = {
        "generated": "2026-09-11T00:00:00Z",
        "lockfile_version": 3,
        "packages": {
            "memory:@zack/m16-reference-memory@0.1.0": {
                "integrity": "local-m16-reference-memory",
                "kind": "memory",
                "name": "@zack/m16-reference-memory",
                "version": "0.1.0",
            },
            "loop:@zack/m16-reference-loop@0.1.0": {
                "integrity": "local-m16-reference-loop",
                "kind": "loop",
                "name": "@zack/m16-reference-loop",
                "version": "0.1.0",
            },
        },
        "roots": {
            "local:agent": {
                "loop": "loop:@zack/m16-reference-loop@0.1.0",
                "memory": ["memory:@zack/m16-reference-memory@0.1.0"],
                "name": "m16-reference-harness-agent",
                "version": "0.1.0",
            }
        },
    }
    (WORKSPACE_ROOT / "agent.lock").write_text(
        json.dumps(lock, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared Harness workspace: {WORKSPACE_ROOT}")
    print(f"Installed memory package: {MEMORY_INSTALL_ROOT}")
    print(f"Installed loop: {LOOP_INSTALL_ROOT}")


if __name__ == "__main__":
    main()
