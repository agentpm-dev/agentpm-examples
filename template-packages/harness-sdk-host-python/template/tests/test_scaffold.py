import json
import pathlib
import unittest


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_includes_harness_sdk_host_files(self) -> None:
        self.assertTrue(pathlib.Path("agentpm.harness.json").exists())
        self.assertTrue(pathlib.Path("app/main.py").exists())
        self.assertTrue(pathlib.Path("reports/.gitkeep").exists())

    def test_harness_config_uses_host_implementations(self) -> None:
        config = json.loads(pathlib.Path("agentpm.harness.json").read_text())
        self.assertEqual(config["model"]["provider"], "python-host-model")
        self.assertEqual(
            config["providers"]["models"]["python-host-model"]["implementation"]["type"],
            "host",
        )
        self.assertEqual(
            config["hooks"]["implementations"]["sdk-before-model"]["implementation"]["type"],
            "host",
        )
        self.assertEqual(config["approvals"]["controller"]["implementation"]["type"], "host")


if __name__ == "__main__":
    unittest.main()
