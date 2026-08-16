from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_workspace_readme_explains_real_workspace_shape(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("agentpm.workspace.json", readme)
        self.assertIn("agents/answer-drafter.agent.json", readme)
        self.assertIn("agents/escalation-reviewer.agent.json", readme)
        self.assertIn("@zack/ops-console", readme)
        self.assertIn("@zack/support-escalation-loop", readme)
        self.assertIn("@zack/support-customer-state", readme)
        self.assertIn("does not add recursive `agents[]`", readme)

    def test_generated_code_has_high_signal_workspace_comments(self) -> None:
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        self.assertIn("teach the generated workspace shape", source)
        self.assertIn("recursive multi-agent orchestration semantics", source)
        self.assertIn("The root app uses its own direct tool dependency here.", source)
        self.assertIn("Installed loop details:", source)

    def test_local_agents_and_sample_thread_exist(self) -> None:
        self.assertTrue((ROOT / "agents" / "answer-drafter.agent.json").exists())
        self.assertTrue((ROOT / "agents" / "escalation-reviewer.agent.json").exists())
        self.assertTrue((ROOT / "sample-inputs" / "support-thread.md").exists())
        self.assertTrue((ROOT / "pyproject.toml").exists())


if __name__ == "__main__":
    unittest.main()
