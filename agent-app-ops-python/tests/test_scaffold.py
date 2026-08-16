from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_runtime_loads_agent_tools_skills_and_generated_manifest(self) -> None:
        source = (ROOT / "app" / "tooling.py").read_text(encoding="utf-8")
        self.assertIn('AGENT_SPEC = "@zack/ops-console@0.1.4"', source)
        self.assertIn('EXTRA_TOOL_NAME = "@zack/summarize-text"', source)
        self.assertIn('load_agent(AGENT_SPEC)', source)
        self.assertIn('from agentpm import (', source)
        self.assertIn("load_loop,", source)
        self.assertIn("def _spec_from_entry(entry: dict[str, Any]) -> str:", source)
        self.assertIn("def load_agent_loop_package(loaded_agent: dict[str, Any]) -> dict[str, Any] | None:", source)
        self.assertIn("def load_agent_memory_packages(loaded_agent: dict[str, Any]) -> list[dict[str, Any]]:", source)
        self.assertIn("def describe_memory_contract(", source)
        self.assertIn('loaded_agent.get("resolvedTools", [])', source)
        self.assertIn('loaded_agent.get("resolvedSkills", [])', source)
        self.assertIn('loaded_agent.get("resolvedMemory", [])', source)
        self.assertIn('entry = loaded_agent.get("resolvedLoop")', source)
        self.assertIn('loaded_skill.get("resolvedTools", [])', source)
        self.assertIn('loaded_skill = load_skill(_spec_from_entry(skill_entry))', source)
        self.assertIn("resolve_extra_tool_spec()", source)
        self.assertIn('load(extra_spec, with_meta=True, env=env)', source)
        self.assertIn("_normalize_csv_query_payload", source)

    def test_runtime_adds_fixture_schema_hint_for_incident_prompts(self) -> None:
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        self.assertIn("FIXTURE_SCHEMA_HINT", source)
        self.assertIn("render_skill_manuals", source)
        self.assertIn("load_agent_loop_package", source)
        self.assertIn("load_agent_memory_packages", source)
        self.assertIn("Loaded loop packages:", source)
        self.assertIn("Authored bindings:", source)
        self.assertIn("Loaded memory packages:", source)
        self.assertIn("Conversation summary contract required fields:", source)
        self.assertIn("Follow these packaged operations manuals", source)
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
        self.assertIn("@zack/incident-response-loop", readme)
        self.assertIn("@zack/conversation-continuity", readme)
        self.assertIn("prepare the next handoff", readme.lower())
        self.assertIn("agentpm install", readme)

    def test_fixture_file_exists(self) -> None:
        self.assertTrue((ROOT / "fixtures" / "incidents.csv").exists())


if __name__ == "__main__":
    unittest.main()
