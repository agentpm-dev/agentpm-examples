from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_harness_configs_are_present_and_secret_free(self) -> None:
        for name in ("agentpm.harness.json", "agentpm.ollama.harness.json"):
            config = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(config["version"], 1)
            self.assertIn("user", config["scopes"])
            self.assertIn("repository", config["scopes"])
            self.assertNotIn("api_key", json.dumps(config).lower())
            self.assertNotIn("token", json.dumps(config).lower())

    def test_readme_documents_preflight_and_headless_paths(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("agentpm harness --json", readme)
        self.assertIn("agentpm harness", readme)
        self.assertIn("--headless", readme)
        self.assertIn("agentpm.ollama.harness.json", readme)
        self.assertIn(".agentpm-state/", readme)

    def test_consumer_context_exists(self) -> None:
        self.assertTrue((ROOT / "maintainer-context.md").exists())


if __name__ == "__main__":
    unittest.main()
