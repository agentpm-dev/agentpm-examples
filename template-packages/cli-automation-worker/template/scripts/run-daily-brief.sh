#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$ROOT_DIR/.tmp"
OUTPUT_PATH="$ROOT_DIR/{{ output_path }}"
SOURCE_PATH="$ROOT_DIR/{{ source_path }}"

if [[ -f "$ROOT_DIR/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.local"
  set +a
fi

mkdir -p "$TMP_DIR"
mkdir -p "$(dirname "$OUTPUT_PATH")"

if [[ ! -f "$SOURCE_PATH" ]]; then
  echo "Source file not found: $SOURCE_PATH" >&2
  exit 1
fi

echo "[1/3] Converting source document..."
python3 - "$ROOT_DIR/inputs/convert.json" "$TMP_DIR/convert-runtime.json" "$SOURCE_PATH" <<'PY'
import json
import sys
from pathlib import Path

template_input_path = Path(sys.argv[1])
runtime_input_path = Path(sys.argv[2])
source_path = Path(sys.argv[3]).resolve()

payload = json.loads(template_input_path.read_text(encoding="utf-8"))
payload["path"] = str(source_path)
runtime_input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

agentpm run @zack/document-convert --input-file "$TMP_DIR/convert-runtime.json" > "$TMP_DIR/converted.json"

echo "[2/3] Preparing summarize-text input..."
python3 - "$TMP_DIR/converted.json" "$TMP_DIR/summary-input.json" <<'PY'
import json
import sys
from pathlib import Path

converted_path = Path(sys.argv[1])
summary_input_path = Path(sys.argv[2])
converted = json.loads(converted_path.read_text(encoding="utf-8"))

if not converted.get("ok"):
    message = converted.get("error", {}).get("message", "document-convert failed")
    raise SystemExit(message)

payload = {
    "text": converted["content"],
    "max_words": 180,
}

summary_input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

echo "[3/3] Running summarization and writing markdown brief..."
agentpm run @zack/summarize-text --input-file "$TMP_DIR/summary-input.json" > "$TMP_DIR/summary.json"

python3 - "$TMP_DIR/summary.json" "$OUTPUT_PATH" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))

if not summary.get("ok"):
    message = summary.get("error", {}).get("message", "summarize-text failed")
    raise SystemExit(message)

output = "\n".join(
    [
        "# {{ workflow_label }}",
        "",
        f"Source: {{ source_path }}",
        "",
        summary["summary"].strip(),
        "",
    ]
)

output_path.write_text(output, encoding="utf-8")
PY

echo "Wrote brief to $OUTPUT_PATH"
