"""Check shell lookup and argument forwarding without inherited tool paths."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="claude launcher ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copy2(ROOT / "claude", self.root / "claude")
        (self.root / "current").write_text("2.1.263\n")
        self.make_executable("downloads/claude-2.1.263", "#!/bin/sh\nexit 0\n")
        self.make_executable("tools/ripgrep/usr/bin/rg", "#!/bin/sh\nexit 0\n")
        self.make_executable("tools/qemu/usr/bin/qemu-x86_64", '''#!/usr/bin/python3
import json, os, shutil, sys
print(json.dumps({"args": sys.argv[1:], "rg": shutil.which("rg"),
                 "updater": os.environ["DISABLE_AUTOUPDATER"],
                 "builtin_rg": os.environ["USE_BUILTIN_RIPGREP"],
                 "cwd": os.getcwd()}))
''')
        self.link = self.root / "bin/claude"
        self.link.parent.mkdir()
        self.link.symlink_to(self.root / "claude")

    def make_executable(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)

    def run_launcher(self, *args):
        return subprocess.run([str(self.link), *args], cwd=self.root,
                              env={"PATH": "/usr/bin:/bin", "HOME": str(self.root)},
                              capture_output=True, text=True, timeout=10)

    def test_symlink_spaces_arguments_and_local_rg(self):
        result = self.run_launcher("-p", "prompt with spaces", "--dangerously-skip-permissions")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["args"], ["-cpu", "max", str(self.root / "downloads/claude-2.1.263"),
                                        "-p", "prompt with spaces", "--dangerously-skip-permissions"])
        self.assertEqual(data["rg"], str(self.root / "tools/ripgrep/usr/bin/rg"))
        self.assertEqual((data["updater"], data["builtin_rg"]), ("1", "0"))
        self.assertEqual(data["cwd"], str(self.root))

    def test_missing_qemu_has_setup_instruction(self):
        (self.root / "tools/qemu/usr/bin/qemu-x86_64").unlink()
        result = self.run_launcher("--version")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("setup.sh", result.stderr)

    def test_invalid_current_is_rejected(self):
        (self.root / "current").write_text("../../unexpected\n")
        result = self.run_launcher("--version")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid current version", result.stderr)


if __name__ == "__main__":
    unittest.main()
