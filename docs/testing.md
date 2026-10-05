# Tests

## Hardware result

Test date: 2026-09-06.

| Item | Value |
| --- | --- |
| CPU | Intel Core 2 Duo P8600, 2.40 GHz |
| OS | Ubuntu 24.04, x86-64 Linux |
| Missing CPU features | POPCNT, SSE4.2, AVX, AVX2 |
| Claude Code | 2.1.263, official linux-x64 binary |
| QEMU | 8.2.2, Ubuntu package 1:8.2.2+ds-0ubuntu1.18 |
| ripgrep | 14.1.0, Ubuntu package 14.1.0-1 |

Without QEMU, GDB stopped at `0x239f731: popcnt %rax,%r14` with SIGILL.
With QEMU, version output, help, theme selection, and login selection worked.
One help run took 6.30 seconds and used 219388 KB of peak resident memory.
This is one measurement, not a general performance estimate.

The verified Claude file contained 215662064 bytes.
Its SHA-256 was:

```text
26d020351e8112f4006790f3cfce43b4c9df0c1bb1d0e542364d64151b81d5ba
```

A clean source copy also passed setup and the local integration test on this CPU.
Setup downloaded QEMU, ripgrep, and Claude without root access.
The test did not use the original installation's downloaded files.
The launcher also passed with only standard system directories in PATH.

## Run checks without downloaded binaries

```bash
python3 build.py
python3 -m unittest discover -s tests
```

These checks cover command lookup, argument handling, file verification, and failed updates.
GitHub Actions runs the same checks. It does not prove compatibility with an old CPU.

## Run the local integration test

First complete the setup and download a Claude release. Then run:

```bash
python3 tests/integration.py
```

The test uses a temporary home, a standard PATH, and a temporary local HTTP service.
It supplies a dummy API key. It does not use your account credentials.
The service sends fixed responses to the real Claude process.

The test checks streamed responses, shell execution, file search, and tool results.
It also checks the final response and process exit status.
The test writes its report to `logs/integration.json`.

This test does not verify Anthropic login or a live model response.
Background sessions, MCP servers, and browser features are not yet verified.

## Report another processor

Include the CPU model, OS, QEMU version, Claude version, and test result.
Remove account data and secrets from logs before you share them.
Do not report hardware support from `--version` alone.

## References

- [Anthropic installer](https://claude.ai/install.sh)
- [Bun CPU requirements](https://bun.sh/docs/installation)
- [Upstream report for CPUs without SSE4.2](https://github.com/anthropics/claude-code/issues/85571)
- [QEMU user-mode documentation](https://www.qemu.org/docs/master/user/main.html)

## Scoped startup result

Test date: 2026-10-05. Same P8600 and QEMU 8.2.2; Claude Code 2.1.289.
A stream-JSON initialization check under a shared one-core quota did not finish
within 70 seconds. Separate-scope checks completed in 28.2 and 24.3 seconds.
A later check with slice CPU weight 200 completed in 22.3 seconds.
These are individual measurements under changing load, not controlled benchmarks.
No model prompt was sent by these initialization checks.
The fast scoped `--version` path completed in 0.04 seconds.

Build checks, 13 unit tests, and the local API integration fixture passed.
The fixture confirmed streaming, shell execution, search, and tool results.
This does not prove a live model conversation or future T3 startup reliability.
