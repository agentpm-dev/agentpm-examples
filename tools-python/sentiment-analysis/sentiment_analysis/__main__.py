import sys, json, pathlib

here = pathlib.Path(__file__).resolve().parent
pkg_root = here.parent
# ensure "summarize_text" is importable as a package
sys.path.insert(0, str(pkg_root))
# vendored pure-Python deps (optional)
_vendor = here / "_vendor"
if _vendor.exists():
    sys.path.insert(0, str(_vendor))

from sentiment_analysis import analyze, ToolError  # absolute import now works


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
