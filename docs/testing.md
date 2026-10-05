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
A second conversation runs `grep` and `find` through Claude's shell functions.
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

## Emulation CPU result

Test date: 2026-10-05. Same P8600 and QEMU 8.2.2; Claude Code 2.1.289.
Each check ran the local API fixture once through QEMU and recorded CPU time.
Other processes used the CPU at the same time. The values are approximate.

| Setting | CPU time (s) | Peak memory (MiB) |
| --- | --- | --- |
| Default (`-cpu max`) | 18.4, 18.3 | 317, 320 |
| `BUN_JSC_useFTLJIT=0` | 17.4, 17.3 | 304, 305 |
| `BUN_JSC_useDFGJIT=0` | 15.5, 14.9, 15.0, 15.4 | 276 to 277 |
| `BUN_JSC_useJIT=0` | 18.7, 18.0 | 244, 246 |
| `-cpu Haswell-v4` | 18.8 | 322 |
| DFG off, one GC marker | 28.2, 26.0 | 283, 285 |
| DFG off, no concurrent GC | 14.6, 14.4 | 276, 277 |

A second series ran with the DFG JIT disabled in all checks. The load was lower.

| Added setting | CPU time (s) | Peak memory (MiB) |
| --- | --- | --- |
| None | 14.5, 14.7, 15.2, 15.3 | 275 to 277 |
| `BUN_GC_TIMER_INTERVAL=5000` | 14.4, 14.7 | 277, 280 |
| `BUN_GC_TIMER_INTERVAL=30000` | 12.7, 13.0 | 288, 289 |
| `BUN_GC_TIMER_DISABLE=1` | 11.8, 12.8, 12.3, 12.8 | 288 to 290 |
| WebAssembly BBQ and OMG off | 14.0, 14.8 | 275 |
| WebAssembly OMG off | 13.7, 15.1 | 275, 276 |
| Baseline JIT later (2000/400) | 14.5, 15.7 | 287, 289 |
| Baseline JIT earlier (200/40) | 19.2, 20.4 | 352, 354 |

The launcher now disables the DFG JIT and sets a 30-second GC timer interval.
The GC timer stays on, so periodic collection continues in long sessions.
Concurrent GC stays on because the gain is small.
GC heap growth factors, generational GC, and mimalloc purge delays changed
CPU time by less than the difference between repeated runs.
An interactive session used 0.09 to 0.13 s of CPU time in 60 idle seconds.
These checks do not measure a long live session.

Each check below used the two launcher settings. Only the QEMU version changed.
QEMU 10.2.1, 11.0.3, and 11.1.2 were static builds from Ubuntu and Debian packages.

| QEMU | CPU time (s) | Peak memory (MiB) |
| --- | --- | --- |
| 8.2.2 (setup default) | 12.7, 12.7 | 289, 290 |
| 10.2.1 | 13.3, 13.2 | 288 |
| 11.0.3 | 13.3, 13.3 | 288, 289 |
| 11.1.2 | 13.5, 13.4 | 292 |

Setup continues to use the Ubuntu 24.04 QEMU package.

## Launcher CPU comparison

Test date: 2026-10-05. Same P8600 and QEMU 8.2.2; Claude Code 2.1.289.
The original and the current `claude` launcher each ran the local API fixture
four times, in alternating order. The table shows the median values.

| Launcher | CPU time (s) | Elapsed time (s) | Peak memory (MiB) |
| --- | --- | --- | --- |
| Original | 17.95 (17.4 to 18.2) | 18.11 | 316 |
| Current | 12.68 (12.5 to 12.7) | 13.24 | 290 |
| Change | -29% | -27% | -8% |

`--version` used 1.2 s of CPU time with both launchers.
This comparison does not include a live model conversation.

## Shell search function result

Test date: 2026-10-05. Same P8600 and QEMU 8.2.2; Claude Code 2.1.289.
Before the fix, `grep` and `find` in the Bash tool stopped with exit code 132.
The local integration test showed the same `Illegal instruction` result.
After the fix, both commands gave the same lines as the system tools.

Each value is CPU time for one call with a warm file cache.

| Command | System tool (s) | Claude function through QEMU (s) |
| --- | --- | --- |
| `grep -n` on one small file | 0.00 | 0.26 to 0.28 |
| `grep -rn` on 753 files, 19 MiB | 0.06 | 0.67 to 0.71 |
| `grep -rn` on 2411 files, 27 MiB | 0.06 to 0.07 | 1.36 to 1.41 |
| `find -name` on 753 files | 0.00 | 0.37 to 0.38 |

Each function call used about 20 to 23 MiB of peak memory.
