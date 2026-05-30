from __future__ import annotations

import unittest
from pathlib import Path

from app.tooling import AGENT_SPEC, build_args_model


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_app_uses_published_ops_console_agent(self) -> None:
        source = (ROOT / "app" / "tooling.py").read_text(encoding="utf-8")
        self.assertEqual(AGENT_SPEC, "@zack/ops-console@0.1.0")
        self.assertIn('load_agent(AGENT_SPEC)', source)
        self.assertIn('loaded_agent.get("resolvedTools", [])', source)

    def test_app_no_longer_requires_local_agent_manifest(self) -> None:
        self.assertFalse((ROOT / "agent.json").exists())

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
        self.assertEqual(fields["body"].annotation, str | None)
        self.assertTrue(fields["action"].is_required())
        self.assertFalse(fields["issue_number"].is_required())


if __name__ == "__main__":
    unittest.main()
