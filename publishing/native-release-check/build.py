"""Compile the helper natively; keep compiler intermediates out of the payload."""

import os
from pathlib import Path
import subprocess
import tempfile


def build_windows(root, output):
    vswhere = (
        Path(os.environ["ProgramFiles(x86)"])
        / "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    installation = subprocess.check_output(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        text=True,
    ).strip()
    if not installation:
        raise RuntimeError(
            "MSVC x64 build tools are required for the Windows native fixture"
        )
    bootstrap = Path(installation) / "VC/Auxiliary/Build/vcvars64.bat"
    with tempfile.TemporaryDirectory(prefix="agentpm-native-build-") as directory:
        temporary = Path(directory)
        script = temporary / "build.cmd"
        # MSVC's static CRT avoids depending on a separately installed VC runtime.
        commands = [
            "@echo off",
            f'call "{bootstrap}"',
            "if errorlevel 1 exit /b 1",
            f'cl /nologo /O2 /MT "{root / "helper.c"}" /Fe:"{output}" /Fo:"{temporary / "helper.obj"}"',
            "exit /b %errorlevel%",
        ]
        script.write_text("\r\n".join(commands) + "\r\n", encoding="utf-8", newline="")
        subprocess.run(["cmd.exe", "/d", "/c", str(script)], cwd=root, check=True)


def build(root):
    root = root.resolve()
    directory = root / "bin"
    directory.mkdir(exist_ok=True)
    output = directory / ("native-helper.exe" if os.name == "nt" else "native-helper")
    if os.name == "nt":
        build_windows(root, output)
    else:
        subprocess.run(
            ["cc", "-O2", str(root / "helper.c"), "-o", str(output)], check=True
        )
    return output


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
