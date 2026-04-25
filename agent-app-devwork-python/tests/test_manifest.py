from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.tooling import build_args_model
from app.workflow import is_write_tool_call


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_manifest_references_tools_with_versions(self) -> None:
        manifest = json.loads((ROOT / "agent.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["kind"], "agent")
        self.assertGreaterEqual(len(manifest["tools"]), 2)
        for entry in manifest["tools"]:
            self.assertIsInstance(entry["name"], str)
            self.assertIsInstance(entry["version"], str)

    def test_build_args_model_marks_non_required_fields_optional(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "issue_number": {"type": "integer"},
                "body": {"type": "string"},
            },
            "required": ["action"],
        }
        model = build_args_model("github-issues", schema)
        fields = model.model_fields
        self.assertEqual(fields["action"].annotation, str)
        self.assertEqual(fields["issue_number"].annotation, int | None)
        self.assertFalse(fields["issue_number"].is_required())

    def test_is_write_tool_call_detects_github_mutations(self) -> None:
        self.assertTrue(
            is_write_tool_call(
                {
                    "name": "github-issues",
                    "args": {"action": "comment_issue"},
                }
            )
        )
        self.assertFalse(
            is_write_tool_call(
                {
                    "name": "github-issues",
                    "args": {"action": "list_issues"},
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
