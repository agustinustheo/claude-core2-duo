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
                 "dfg": os.environ["BUN_JSC_useDFGJIT"],
                 "gc_ms": os.environ["BUN_GC_TIMER_INTERVAL"],
                 "prefix": os.environ.get("CLAUDE_CODE_SHELL_PREFIX"),
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

    def run_launcher(self, *args, **extra):
        return subprocess.run([str(self.link), *args], cwd=self.root,
                              env={"PATH": "/usr/bin:/bin", "HOME": str(self.root), **extra},
                              capture_output=True, text=True, timeout=10)

    def test_symlink_spaces_arguments_and_local_rg(self):
        result = self.run_launcher("-p", "prompt with spaces", "--dangerously-skip-permissions")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["args"], ["-cpu", "max", str(self.root / "downloads/claude-2.1.263"),
                                        "-p", "prompt with spaces", "--dangerously-skip-permissions"])
        self.assertEqual(data["rg"], str(self.root / "tools/ripgrep/usr/bin/rg"))
        self.assertEqual((data["updater"], data["builtin_rg"]), ("1", "0"))
        self.assertEqual((data["dfg"], data["gc_ms"]), ("0", "30000"))
        self.assertEqual(data["cwd"], str(self.root))

    def test_engine_settings_can_be_restored(self):
        result = self.run_launcher("--version", BUN_JSC_useDFGJIT="1", BUN_GC_TIMER_INTERVAL="1000")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual((data["dfg"], data["gc_ms"]), ("1", "1000"))

    def test_shell_prefix_default_and_override(self):
        data = json.loads(self.run_launcher("--version").stdout)
        self.assertEqual(data["prefix"], str(self.root / "claude-shell"))
        data = json.loads(self.run_launcher("--version", CLAUDE_CODE_SHELL_PREFIX="/opt/log").stdout)
        self.assertEqual(data["prefix"], "/opt/log")

    def test_embedded_search_tools_keep_their_names(self):
        binary = str(self.root / "downloads/claude-2.1.263")
        ugrep = ["-G", "--ignore-files", "--hidden", "-I", "--exclude-dir=.git", "-rn", "a b"]
        bfs = ["-S", "dfs", "-regextype", "findutils-default", ".", "-name", "*.txt"]
        for name, args in (("ugrep", ugrep), ("bfs", bfs)):
            result = self.run_launcher(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["args"], ["-cpu", "max", "-0", name, binary, *args])
        result = self.run_launcher("-G", "--ignore-files")
        self.assertEqual(json.loads(result.stdout)["args"], ["-cpu", "max", binary, "-G", "--ignore-files"])

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
