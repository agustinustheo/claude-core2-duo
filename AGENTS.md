# Agent instructions

Read README.md and CONTRIBUTING.md before editing.
Keep runtime files under downloads/ and tools/. Do not commit them.
Keep account data, logs, and local link backups out of Git.
Do not edit user shell configuration unless the task requires it.

Use Python's standard library and Bash. Keep each function focused on one task.
Preserve checksum validation, the update lock, and atomic version selection.
Preserve the caller's working directory and argument boundaries.

Run python3 build.py and python3 -m unittest discover -s tests.
For runtime changes, run python3 tests/integration.py after setup.
Use a standard system PATH in tests. Do not rely on agent-provided binaries.
Do not claim a live account test from a local API fixture.

Write short documentation in ASD-STE100 Simplified Technical English.
Record known faults in docs/troubleshooting.md and hardware results in docs/testing.md.
