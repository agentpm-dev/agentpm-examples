import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json

SPEC = importlib.util.spec_from_file_location(
    "release_examples", Path(__file__).with_name("release_examples.py")
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseExamplesTests(unittest.TestCase):
    def test_each_tag_selects_only_its_package_and_exact_version(self):
        for name, path in release.PACKAGES.items():
            manifest = json.loads((release.ROOT / path / "agent.json").read_text())
            value = release.select(f'{name}/v{manifest["version"]}', "fixture")
            self.assertEqual(value["package_dir"], path)
            self.assertEqual(value["ref"], f'@fixture/{name}@{manifest["version"]}')
        for tag in [
            "v0.1.0",
            "summarize-text/v999.0.0",
            "devwork-copilot/v",
            "other/v0.1.0",
        ]:
            with self.assertRaises(ValueError):
                release.select(tag, "fixture")
        with self.assertRaises(ValueError):
            release.select("summarize-text/v0.1.9", "bad\nnamespace")

    def test_agent_verification_requires_exact_tool_versions_without_launching_sdk(
        self,
    ):
        manifest = json.loads(
            (
                release.ROOT / release.PACKAGES["devwork-copilot"] / "agent.json"
            ).read_text()
        )
        packages = {
            "agent": {
                "name": "@fixture/devwork-copilot",
                "version": manifest["version"],
            }
        }
        packages.update({str(i): tool for i, tool in enumerate(manifest["tools"])})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.lock"
            path.write_text(json.dumps({"packages": packages}))
            with patch.object(release.subprocess, "run") as execute:
                release.verify(
                    "devwork-copilot",
                    f'@fixture/devwork-copilot@{manifest["version"]}',
                    Path(directory),
                )
                execute.assert_not_called()
            packages["0"] = dict(packages["0"], version="999.0.0")
            path.write_text(json.dumps({"packages": packages}))
            with self.assertRaises(ValueError):
                release.verify(
                    "devwork-copilot",
                    f'@fixture/devwork-copilot@{manifest["version"]}',
                    Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
