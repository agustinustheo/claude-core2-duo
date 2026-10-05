"""Check that Claude's grep and find shell functions do not start the native binary."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Bash branch of the functions in Claude Code 2.1.289 shell snapshots.
FUNCTIONS = '''
function find {
  local _cc_bin="${CLAUDE_CODE_EXECPATH:-}"
  [[ -x $_cc_bin ]] || _cc_bin=/nonexistent/claude
  if [[ ! -x $_cc_bin ]]; then command find ${1+"$@"}; return; fi
  (exec -a bfs "$_cc_bin" -S dfs -regextype findutils-default ${1+"$@"})
}
function grep {
  local _cc_bin="${CLAUDE_CODE_EXECPATH:-}"
  [[ -x $_cc_bin ]] || _cc_bin=/nonexistent/claude
  if [[ ! -x $_cc_bin ]]; then command grep ${1+"$@"}; return; fi
  (exec -a ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl ${1+"$@"})
}
'''


class ShellPrefixTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="claude shell ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("claude", "claude-shell"):
            shutil.copy2(ROOT / name, self.root / name)
        (self.root / "current").write_text("2.1.263\n")
        # The native binary stops with SIGILL, as on a CPU without POPCNT.
        self.native = self.make_executable("downloads/claude-2.1.263", "#!/bin/sh\nkill -ILL $$\n")
        self.make_executable("tools/ripgrep/usr/bin/rg", "#!/bin/sh\nexit 0\n")
        self.make_executable("tools/qemu/usr/bin/qemu-x86_64",
                             '#!/bin/sh\nprintf "%s|" "$@"\n')
        self.snapshot = self.root / "snapshot.sh"
        self.snapshot.write_text(FUNCTIONS)

    def make_executable(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)
        return path

    def run_command(self, command, prefix=True):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root), "SHELL": "/bin/bash",
               "CLAUDE_CODE_EXECPATH": str(self.native)}
        line = f"source '{self.snapshot}' && {command}"
        argv = [str(self.root / "claude-shell"), line] if prefix else ["bash", "-c", line]
        return subprocess.run(argv, cwd=self.root, env=env, capture_output=True, text=True, timeout=10)

    def test_without_prefix_functions_crash(self):
        self.assertEqual(self.run_command("grep -n x file", prefix=False).returncode, 132)

    def test_functions_run_under_qemu(self):
        native = str(self.native)
        result = self.run_command("grep -n 'a b' file")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith(f"-cpu|max|-0|ugrep|{native}|-G|--ignore-files|"))
        self.assertTrue(result.stdout.endswith("|-n|a b|file|"))
        result = self.run_command("find . -name '*.txt'")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"-cpu|max|-0|bfs|{native}|-S|dfs|-regextype|findutils-default|.|-name|*.txt|")

    def test_prefix_keeps_status_and_directory(self):
        result = self.run_command("cd downloads && pwd -P && exit 7")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.strip(), str((self.root / "downloads").resolve()))


if __name__ == "__main__":
    unittest.main()
