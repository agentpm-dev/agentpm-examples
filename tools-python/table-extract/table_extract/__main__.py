from __future__ import annotations

import json
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent))

from table_extract import ToolError, extract_tables


def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    try:
        out = extract_tables(**payload)
        sys.stdout.write(json.dumps({"ok": True, **out}))
    except ToolError as exc:
        sys.stdout.write(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc)}}))
        sys.exit(0)
    except Exception as exc:  # pragma: no cover
        sys.stdout.write(json.dumps({"ok": False, "error": {"code": "UNEXPECTED", "message": str(exc)}}))
        sys.exit(1)


if __name__ == "__main__":
    main()
