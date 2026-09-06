#!/usr/bin/env python3
"""Fetch an official release and activate it only after verification."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = "https://downloads.claude.ai/claude-code-releases"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def fetch(path):
    """Read release metadata over HTTPS with a bounded socket wait."""
    with urllib.request.urlopen(BASE + "/" + path, timeout=60) as response:
        return response.read()


def parse_manifest(raw, version):
    """Reject malformed metadata before it controls a download or path."""
    metadata = json.loads(raw)
    if not isinstance(metadata, dict) or metadata.get("version") != version:
        raise ValueError("Manifest version mismatch")
    platform = metadata["platforms"]["linux-x64"]
    checksum, size = platform["checksum"], platform["size"]
    if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
        raise ValueError("Invalid SHA-256 in manifest")
    if type(size) is not int or size <= 0:
        raise ValueError("Invalid file size in manifest")
    return platform


def verified(path, metadata):
    if not path.is_file() or path.stat().st_size != metadata["size"]:
        return False
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest() == metadata["checksum"]


def download_binary(version, destination, metadata):
    """Keep partial or corrupt files away from the executable path."""
    fd, name = tempfile.mkstemp(prefix=".download-", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output, urllib.request.urlopen(
            BASE + "/" + version + "/linux-x64/claude", timeout=60
        ) as source:
            size = 0
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                if size > metadata["size"]:
                    raise ValueError("Download exceeds manifest size")
                output.write(chunk)
        if not verified(temporary, metadata):
            raise ValueError("Official SHA-256 or size verification failed")
        temporary.chmod(0o755)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def smoke_check(root, binary, version):
    result = subprocess.run(
        [str(root / "tools/qemu/usr/bin/qemu-x86_64"), "-cpu", "max", str(binary), "--version"],
        capture_output=True, text=True, check=True, timeout=120,
        env={**os.environ, "DISABLE_AUTOUPDATER": "1"},
    )
    if result.stdout.strip() != version + " (Claude Code)":
        raise ValueError("Unexpected version output: " + result.stdout.strip())


def atomic_write(path, data):
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def activate(root, version):
    current = root / "current"
    new = (version + "\n").encode()
    if current.exists() and current.read_bytes() != new:
        atomic_write(root / "previous", current.read_bytes())
    atomic_write(current, new)


def update(root, target):
    if target not in ("latest", "stable") and not VERSION.fullmatch(target):
        raise ValueError("Use latest, stable, or a version such as 2.1.263")
    if not os.access(root / "tools/qemu/usr/bin/qemu-x86_64", os.X_OK):
        raise ValueError("Missing QEMU. Run bash setup.sh first")
    downloads = root / "downloads"
    downloads.mkdir(exist_ok=True)
    with (root / ".update.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        version = fetch(target).decode().strip() if target in ("latest", "stable") else target
        if not VERSION.fullmatch(version):
            raise ValueError("Invalid version from release service")
        manifest = fetch(version + "/manifest.json")
        metadata = parse_manifest(manifest, version)
        binary = downloads / ("claude-" + version)
        if not verified(binary, metadata):
            print("Downloading Claude Code " + version, flush=True)
            download_binary(version, binary, metadata)
        binary.chmod(0o755)
        smoke_check(root, binary, version)
        atomic_write(downloads / (version + "-manifest.json"), manifest)
        activate(root, version)
    print(version + " (Claude Code) activated; official SHA-256 verified.")
    print("Launch with " + str(root / "claude"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default="latest", help="latest, stable, or VERSION")
    args = parser.parse_args()
    try:
        update(ROOT, args.target)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, "Update failed: " + str(error) + "\n")


if __name__ == "__main__":
    main()
