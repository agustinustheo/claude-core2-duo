#!/usr/bin/env python3
"""Check all project scripts without downloads or credentials."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
sources = sorted(root.glob("*.py")) + sorted((root / "tests").glob("*.py"))
for source in sources:
    compile(source.read_text(), str(source), "exec")
for name in ("claude", "claude-scoped", "claude-shell", "setup.sh"):
    subprocess.run(["bash", "-n", str(root / name)], check=True)
print("Build checks passed.")
