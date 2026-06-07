from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_script_uses_agentpm_run_with_input_files(self) -> None:
        source = (ROOT / "scripts" / "run-daily-brief.sh").read_text(encoding="utf-8")
        self.assertIn("agentpm run @zack/document-convert --input-file", source)
        self.assertIn("agentpm run @zack/summarize-text --input-file", source)
        self.assertIn("convert-runtime.json", source)
        self.assertIn('if not converted.get("ok")', source)
        self.assertIn('if not summary.get("ok")', source)
        self.assertIn('"$TMP_DIR/summary-input.json"', source)
        self.assertIn("Wrote brief to $OUTPUT_PATH", source)

    def test_scaffold_keeps_template_variables_meaningful(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("zack-worker", readme)
        self.assertIn("sample-inputs/daily-notes.md", readme)
        self.assertIn("outputs/daily-brief.md", readme)

    def test_sample_input_and_json_payload_exist(self) -> None:
        self.assertTrue((ROOT / "sample-inputs" / "daily-notes.md").exists())
        self.assertTrue((ROOT / "inputs" / "convert.json").exists())


if __name__ == "__main__":
    unittest.main()
