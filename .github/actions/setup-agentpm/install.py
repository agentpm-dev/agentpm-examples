"""Install one pinned released CLI using native filesystem paths on every runner."""

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import zipfile

TARGETS = {
    ("Linux", "X64"): "x86_64-unknown-linux-gnu",
    ("macOS", "ARM64"): "aarch64-apple-darwin",
    ("macOS", "X64"): "x86_64-apple-darwin",
    ("Windows", "X64"): "x86_64-pc-windows-msvc",
}


def install():
    version = os.environ.get("AGENTPM_CLI_VERSION", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError(
            "Set AGENTPM_CLI_VERSION to an exact released CLI version with package/headless signing support."
        )
    target = TARGETS.get((os.environ["RUNNER_OS"], os.environ["RUNNER_ARCH"]))
    if target is None:
        raise ValueError("Unsupported example runner")
    windows = os.environ["RUNNER_OS"] == "Windows"
    extension = "zip" if windows else "tar.gz"
    name = f"agentpm-{target}.{extension}"
    destination = Path(os.environ["RUNNER_TEMP"]) / "agentpm-cli"
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "gh",
            "release",
            "download",
            f"v{version}",
            "--repo",
            "agentpm-dev/cli",
            "--pattern",
            name,
            "--pattern",
            f"agentpm-{target}.sha256",
            "--dir",
            str(destination),
        ],
        check=True,
    )
    fields = (
        (destination / f"agentpm-{target}.sha256").read_text(encoding="utf-8").split()
    )
    if (
        len(fields) != 2
        or not re.fullmatch(r"[a-fA-F0-9]{64}", fields[0])
        or PurePosixPath(fields[1].replace("\\", "/")).name != name
    ):
        raise ValueError("Invalid CLI release checksum record")
    source = destination / name
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != fields[0].lower():
        raise ValueError("CLI release checksum mismatch")
    binary = destination / ("agentpm.exe" if windows else "agentpm")
    # Extract only the expected executable; platform ZIP/tar formats differ,
    # but the download's checksum is always verified before extraction.
    if windows:
        with zipfile.ZipFile(source) as archive:
            with archive.open(binary.name) as stream, binary.open("wb") as output:
                shutil.copyfileobj(stream, output)
    else:
        with tarfile.open(source, "r:gz") as archive:
            member = archive.getmember(binary.name)
            if not member.isfile():
                raise ValueError("CLI release executable must be a regular file")
            with archive.extractfile(member) as stream, binary.open("wb") as output:
                shutil.copyfileobj(stream, output)
    binary.chmod(0o755)
    actual = subprocess.check_output([str(binary), "--version"], text=True).strip()
    if actual != f"agentpm {version}":
        raise ValueError("CLI executable version differs from the selected release")
    subprocess.run(
        [str(binary), "package", "--help"], stdout=subprocess.DEVNULL, check=True
    )
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as output:
        output.write(str(destination.resolve()) + "\n")


if __name__ == "__main__":
    try:
        install()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
