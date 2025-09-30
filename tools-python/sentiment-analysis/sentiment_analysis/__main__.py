import sys, json, pathlib

# add vendored deps to path
_vendor = pathlib.Path(__file__).parent / "_vendor"
if _vendor.exists():
    sys.path.insert(0, str(_vendor))

from . import analyze, ToolError  # uses the function defined in __init__.py


def main():
    payload = json.loads(sys.stdin.read() or "{}")
    try:
        out = analyze(**payload)
        sys.stdout.write(json.dumps({"ok": True, **out}))
    except ToolError as te:
        err = {"code": te.code, "message": str(te)}
        if te.details is not None:
            err["details"] = te.details
        sys.stdout.write(json.dumps({"ok": False, "error": err}))
        # value-level error -> exit code 0
        sys.exit(0)
    except Exception as e:
        sys.stdout.write(json.dumps({
            "ok": False,
            "error": {"code": "UNEXPECTED", "message": str(e)}
        }))
        # unexpected/transport error -> non-zero
        sys.exit(1)

if __name__ == "__main__":
    main()
