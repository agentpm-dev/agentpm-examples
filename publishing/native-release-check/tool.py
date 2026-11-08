"""Call the helper compiled on the publishing runner."""

import json
from pathlib import Path
import subprocess
import sys

value = json.load(sys.stdin)["value"]
if type(value) is not int or not -1000 <= value <= 1000:
    raise ValueError("value must be an integer between -1000 and 1000")
helper = Path(__file__).resolve().with_name("bin") / (
    "native-helper.exe" if sys.platform == "win32" else "native-helper"
)
result = subprocess.run(
    [str(helper), str(value)], check=True, capture_output=True, text=True
)
print(json.dumps({"value": int(result.stdout)}))
