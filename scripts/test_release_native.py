"""Native fixture layout and Windows compiler/entrypoint setup contracts."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "publishing/native-release-check"
SPEC = importlib.util.spec_from_file_location("native_build", FIXTURE / "build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class NativeReleaseTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("cc"), "requires a native C compiler")
    def test_compiled_helper_and_python_entrypoint_use_the_manifest_payload_layout(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["helper.c", "tool.py"]:
                shutil.copyfile(FIXTURE / name, root / name)
            executable = build.build(root)
            self.assertTrue(executable.is_file())
            self.assertEqual(executable.parent.name, "bin")
            output = subprocess.run(
                [sys.executable, str(root / "tool.py")],
                input='{"value":3}',
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(output.stdout), {"value": 4})
            self.assertEqual(len(list((root / "bin").iterdir())), 1)
        manifest = json.loads((FIXTURE / "agent.json").read_text())
        self.assertIn("bin", manifest["files"])
        self.assertNotIn("native-helper.exe", manifest["files"])

    def test_windows_entrypoint_selects_the_exe_in_the_same_bin_directory(self):
        with patch.object(sys, "platform", "win32"), patch.object(
            sys, "stdin", io.StringIO('{"value":3}')
        ):
            with patch.object(
                subprocess, "run", return_value=SimpleNamespace(stdout="4\n")
            ) as execute:
                output = io.StringIO()
                with redirect_stdout(output):
                    runpy.run_path(str(FIXTURE / "tool.py"), run_name="__main__")
        self.assertEqual(
            Path(execute.call_args.args[0][0]), FIXTURE / "bin/native-helper.exe"
        )
        self.assertEqual(json.loads(output.getvalue()), {"value": 4})

    def test_windows_build_bootstraps_x64_msvc_and_keeps_objects_out_of_payload(self):
        scripts = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "bin/native-helper.exe"

            def run(command, **_):
                self.assertEqual(command[:3], ["cmd.exe", "/d", "/c"])
                scripts.append(Path(command[3]).read_bytes().decode())

            with patch.dict(
                os.environ, {"ProgramFiles(x86)": str(root / "Program Files (x86)")}
            ):
                with patch.object(
                    subprocess,
                    "check_output",
                    return_value=str(root / "Visual Studio") + "\n",
                ) as locate:
                    with patch.object(subprocess, "run", side_effect=run):
                        build.build_windows(root, output)
            self.assertIn(
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                locate.call_args.args[0],
            )
            self.assertIn('vcvars64.bat"', scripts[0])
            self.assertIn("/MT", scripts[0])
            self.assertIn(f'/Fe:"{output}"', scripts[0])
            self.assertIn("helper.obj", scripts[0])
            self.assertIn("\r\n", scripts[0])
            self.assertNotIn(f'/Fo:"{root / "bin"}', scripts[0])


if __name__ == "__main__":
    unittest.main()
