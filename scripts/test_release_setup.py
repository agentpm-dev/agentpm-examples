"""Execute the composite installer against local release assets and a fake gh."""

import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import textwrap
import unittest
import zipfile

ACTION = (
    Path(__file__).resolve().parents[1] / ".github/actions/setup-agentpm/action.yml"
)


class SetupActionTests(unittest.TestCase):
    def run_setup(self, checksum="valid", version="0.1.41", windows=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            target = "x86_64-pc-windows-msvc" if windows else "x86_64-unknown-linux-gnu"
            archive = assets / f"agentpm-{target}.{'zip' if windows else 'tar.gz'}"
            content = (
                b'#!/bin/sh\nif [ "$1" = --version ]; then echo "agentpm 0.1.41"; fi\n'
            )
            if windows:
                with zipfile.ZipFile(archive, "w") as output:
                    output.writestr("agentpm.exe", content)
            else:
                with tarfile.open(archive, "w:gz") as output:
                    header = tarfile.TarInfo("agentpm")
                    header.size = len(content)
                    header.mode = 0o755
                    output.addfile(header, io.BytesIO(content))
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            record = f"{digest}  dist/{archive.name}\n"
            if windows:
                record = f"{digest.upper()}  dist\\{archive.name}\n"
            if checksum == "wrong":
                record = f'{"0" * 64}  dist/{archive.name}\n'
            elif checksum == "wrong-name":
                record = f"{digest}  different.tar.gz\n"
            (assets / f"agentpm-{target}.sha256").write_text(record)
            commands = root / "commands"
            commands.mkdir()
            gh = commands / "gh"
            gh.write_text(
                "#!/usr/bin/env python3\n"
                "import os, pathlib, shutil, sys\n"
                "assert sys.argv[1:4] == ['release', 'download', 'v0.1.41']\n"
                "target = pathlib.Path(sys.argv[sys.argv.index('--dir')+1])\n"
                "for path in pathlib.Path(os.environ['FIXTURE_ASSETS']).iterdir():\n"
                "    shutil.copyfile(path, target/path.name)\n"
            )
            gh.chmod(0o755)
            script = textwrap.dedent(ACTION.read_text().split("      run: |\n", 1)[1])
            environment = {
                **os.environ,
                "PATH": str(commands) + os.pathsep + os.environ["PATH"],
                "RUNNER_TEMP": str(root / "runner"),
                "RUNNER_OS": "Windows" if windows else "Linux",
                "RUNNER_ARCH": "X64",
                "AGENTPM_CLI_VERSION": version,
                "ACTION_INSTALLER": str(ACTION.with_name("install.py")),
                "FIXTURE_ASSETS": str(assets),
                "GITHUB_PATH": str(root / "github-path"),
            }
            result = subprocess.run(
                ["bash"],
                input=script,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            return result, (root / "github-path").exists()

    def test_dist_prefixed_release_checksum_and_install_succeed(self):
        result, installed = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(installed)

    def test_windows_zip_backslash_checksum_and_exe_path(self):
        # POSIX executable fixture inside a Windows-format ZIP: validates the
        # actual installer branch without claiming Windows PE execution here.
        result, installed = self.run_setup(windows=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(installed)

    def test_windows_checksum_mismatch_never_installs(self):
        result, installed = self.run_setup("wrong", windows=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertFalse(installed)

    def test_checksum_mismatch_never_installs(self):
        result, installed = self.run_setup("wrong")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertFalse(installed)

    def test_wrong_checksum_filename_never_installs(self):
        result, installed = self.run_setup("wrong-name")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid CLI release checksum record", result.stderr)
        self.assertFalse(installed)

    def test_missing_or_injected_version_fails_before_download(self):
        for version in ["", "latest", "0.1.41; echo injected"]:
            result, installed = self.run_setup(version=version)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact released CLI version", result.stderr)
            self.assertFalse(installed)


if __name__ == "__main__":
    unittest.main()
