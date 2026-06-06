from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_runtime_loads_tools_from_published_agent_and_generated_manifest(self) -> None:
        source = (ROOT / "app" / "tooling.py").read_text(encoding="utf-8")
        self.assertIn('AGENT_SPEC = "@zack/ops-console@0.1.0"', source)
        self.assertIn('EXTRA_TOOL_NAME = "@zack/summarize-text"', source)
        self.assertIn('load_agent(AGENT_SPEC)', source)
        self.assertIn('loaded_agent.get("resolvedTools", [])', source)
        self.assertIn("resolve_extra_tool_spec()", source)
        self.assertIn('load(extra_spec, with_meta=True, env=env)', source)
        self.assertIn("_normalize_csv_query_payload", source)

    def test_runtime_adds_fixture_schema_hint_for_incident_prompts(self) -> None:
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        self.assertIn("FIXTURE_SCHEMA_HINT", source)
        self.assertIn("Do not use alternate names like id, description, or created_at.", source)
        self.assertIn("not symbolic operators like =.", source)
        self.assertIn("augment_user_prompt", source)

    def test_csv_query_symbolic_ops_are_normalized_in_wrapper(self) -> None:
        source = (ROOT / "app" / "tooling.py").read_text(encoding="utf-8")
        self.assertIn('"=": "eq"', source)
        self.assertIn('">=": "gte"', source)
        self.assertIn('not Path(path).is_absolute()', source)
        self.assertIn('payload = _normalize_csv_query_payload(_tool_name, payload)', source)

    def test_readme_keeps_fixture_first_story(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("fixtures/incidents.csv", readme)
        self.assertIn("zack-worker", readme)
        self.assertIn("@zack/ops-console", readme)
        self.assertIn("agentpm install", readme)

    def test_fixture_file_exists(self) -> None:
        self.assertTrue((ROOT / "fixtures" / "incidents.csv").exists())


if __name__ == "__main__":
    unittest.main()
