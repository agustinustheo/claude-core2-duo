"""Offline tests for downloads, release selection, and failed updates."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="claude tests ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "downloads").mkdir()
        qemu = self.root / "tools/qemu/usr/bin/qemu-x86_64"
        qemu.parent.mkdir(parents=True)
        qemu.write_text("#!/bin/sh\nexit 0\n")
        qemu.chmod(0o755)
        (self.root / "current").write_text("2.1.100\n")
        self.payload = b"official binary fixture"
        self.metadata = {"size": len(self.payload), "checksum": hashlib.sha256(self.payload).hexdigest()}
        self.manifest = json.dumps({"version": "2.1.263", "platforms": {"linux-x64": self.metadata}}).encode()
        self.binary = self.root / "downloads/claude-2.1.263"

    def test_verified_checks_size_and_hash(self):
        self.assertFalse(update.verified(self.binary, self.metadata))
        self.binary.write_bytes(self.payload)
        self.assertTrue(update.verified(self.binary, self.metadata))
        self.binary.write_bytes(b"x" * len(self.payload))
        self.assertFalse(update.verified(self.binary, self.metadata))

    def test_download_failure_preserves_existing_file(self):
        self.binary.write_bytes(b"old file")
        for payload in (b"bad", b"x" * len(self.payload), self.payload + b"extra"):
            with self.subTest(payload=payload), patch("update.urllib.request.urlopen", return_value=io.BytesIO(payload)):
                with self.assertRaises(ValueError):
                    update.download_binary("2.1.263", self.binary, self.metadata)
                self.assertEqual(self.binary.read_bytes(), b"old file")
                self.assertEqual(list(self.binary.parent.glob(".download-*")), [])

    def test_download_and_activate(self):
        with patch("update.fetch", return_value=self.manifest), patch(
            "update.urllib.request.urlopen", return_value=io.BytesIO(self.payload)
        ), patch("update.smoke_check") as smoke:
            update.update(self.root, "2.1.263")
        smoke.assert_called_once_with(self.root, self.binary, "2.1.263")
        self.assertEqual((self.root / "current").read_text(), "2.1.263\n")
        self.assertEqual((self.root / "previous").read_text(), "2.1.100\n")

    def test_failed_smoke_check_does_not_activate(self):
        self.binary.write_bytes(self.payload)
        with patch("update.fetch", return_value=self.manifest), patch(
            "update.smoke_check", side_effect=subprocess.CalledProcessError(132, "qemu")
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                update.update(self.root, "2.1.263")
        self.assertEqual((self.root / "current").read_text(), "2.1.100\n")
        self.assertFalse((self.root / "previous").exists())

    def test_same_version_keeps_previous(self):
        update.activate(self.root, "2.1.263")
        update.activate(self.root, "2.1.263")
        self.assertEqual((self.root / "previous").read_text(), "2.1.100\n")

    def test_bad_version_rejected_before_network(self):
        with patch("update.fetch") as fetch:
            for version in ("../escape", "1.2.3/../../escape", "", "2.1.263\n"):
                with self.subTest(version=version), self.assertRaises(ValueError):
                    update.update(self.root, version)
            fetch.assert_not_called()

    def test_bad_channel_response_rejected(self):
        with patch("update.fetch", return_value=b"<html>error</html>"):
            with self.assertRaises(ValueError):
                update.update(self.root, "latest")
        self.assertEqual((self.root / "current").read_text(), "2.1.100\n")

    def test_invalid_manifest_rejected(self):
        for size, checksum in ((0, "a" * 64), (True, "a" * 64), (1, "bad")):
            raw = json.dumps({"version": "2.1.263", "platforms": {"linux-x64": {"size": size, "checksum": checksum}}})
            with self.subTest(size=size, checksum=checksum), self.assertRaises(ValueError):
                update.parse_manifest(raw, "2.1.263")
        with self.assertRaises(ValueError):
            update.parse_manifest(self.manifest, "2.1.100")
        with self.assertRaises(ValueError):
            update.parse_manifest(b"[]", "2.1.263")


if __name__ == "__main__":
    unittest.main()
