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

## Provider status investigation

Test date: 2026-10-10. Intel Core 2 Duo P8600, Claude Code 2.1.295,
and T3 0.0.45. The scoped launcher had no slice CPU quota.

Two direct stream-JSON initialization checks returned account information
in 17.6 and 14.3 seconds. Both disabled hooks and MCP connections, as the
T3 capability probe does. The second used the T3 server environment and
working directory, with a standard system PATH.
These checks did not send a model prompt or use the T3 SDK itself.

The installed T3 code sets a 25-second capability probe deadline and caches
the result for five minutes. It also caches failed results and hides the
probe error. A timeout is a possible cause of the provider warning, but
these checks did not reproduce that failure.

## New session startup investigation

Test date: 2026-10-11. Same P8600; Claude Code 2.1.295, QEMU 8.2.2,
Codex 0.162.0, and T3 0.0.45.

The T3 service and Codex shared a 100% CPU quota, equal to one core.
The service CPU weight was 50. Claude ran in a separate slice with no quota
and CPU weight 200. The host had 5.7 GiB of available memory and no swap use.
The service had recorded 35.3 seconds of CPU throttling since startup.

The trace showed a Codex provider probe interrupted after 11.1 seconds at
T3 startup. The full status check took 13.8 seconds, including cleanup.
The Claude status check took 31.3 seconds. The trace does not expose the
Claude probe error. Git and pull request checks also ran during startup.

A later direct Codex check completed initialization, account lookup, skills,
models, and rate limits in 2.0 seconds. A T3 Codex session started in 2.7 seconds.
These values do not include model response time.

Direct Claude initialization took 14.2 seconds with hooks and MCP connections
disabled. With the running T3 Claude environment and a project directory,
initialization took 20.3 seconds. The checks used different settings and
directories. They are not a controlled comparison.
The project check found 11 enabled plugins and many MCP servers with
`needs-auth` or `failed` status. A SessionStart hook failed because it called
`python`, which was not available. The host provides `python3`.

A resumed T3 Claude session took 47.9 seconds from session creation to
`status:requesting`. This interval can include initialization, session restore,
hooks, and MCP connections. It does not isolate one cause.

No model prompt was sent by the direct checks. They do not prove a live
account conversation. Build checks and 19 unit tests passed with a standard
system PATH. No launcher code changed.

## Fast MCP startup profile

Test date: 2026-10-11. Same P8600, Claude Code 2.1.295, and QEMU 8.2.2.
The scoped launcher now reads an optional local `tools/startup-profile` file.
The `fast` profile disables automatic cloud and plugin MCP connections.
It keeps built-in tools, skills, hooks, and explicit MCP configurations.

One baseline initialization check took 18.6 seconds and listed 42 MCP servers.
Two checks through a temporary fast-profile launcher took 17.8 and 17.4 seconds.
The second check included an explicit local MCP fixture named `t3-code`.
Only that server was listed, and its status was `connected`.
The selected scoped launcher then took 19.3 seconds and listed no MCP servers.
A local integration test ran at the same time as that last check.
These measurements do not establish a consistent startup speed increase.
They confirm that automatic MCP connections are excluded.

Account metadata was present in each initialization result. No model prompt
was sent by these checks. The explicit MCP fixture does not test T3's live
MCP service. Build checks, 20 unit tests, and the standard local API integration
test passed. The same API fixture also passed through the selected scoped
launcher. That check supplied the systemd user runtime directory and used a
standard system PATH. It checked streaming, shell execution, file search,
and the emulated `grep` and `find` functions.
The fixture does not prove a live account conversation.

## Fresh T3 provider status checks

Test date: 2026-10-11. Same P8600, T3 0.0.45, Claude Code 2.1.295,
QEMU 8.2.2, and Codex 0.162.0. The fast MCP profile remained selected.

Both displayed status snapshots still had boot-time `checkedAt` values
when checked more than one hour later. No later authentication probe was
present in the inspected trace. Workspace refreshes did not replace them.

The installed T3 CLI issued a short-lived local diagnostic session.
An authenticated WebSocket request refreshed each provider by `instanceId`,
without a `cwd`. The requests ran in sequence.

| Provider | Full status check (s) | Status | Authentication | Models |
| --- | --- | --- | --- | --- |
| Codex | 2.01 | ready | authenticated | 8 |
| Claude | 25.89 | ready | authenticated | 13 |

T3 saved both new status snapshots. The Claude process used the selected
fast profile and strict MCP configuration. The full Claude status check
includes work after initialization, so 25.89 seconds does not mean that
its 25-second initialization deadline failed.

These were real T3 status checks with the current account configuration.
They did not send a model prompt or test a live model conversation.
The startup deadlines and service CPU quota did not change. Startup load
can still cause another timeout.

## Automatic provider status refresh

Test date: 2026-10-11. Same P8600, T3 0.0.45, Claude Code 2.1.295,
QEMU 8.2.2, and Codex 0.162.0. The fast MCP profile remained selected.

A manual run of `t3-refresh-providers --now` used a standard system PATH.
It took 25.5 seconds in total and revoked its T3 session.

| Provider | Status check (s) | Status | Authentication | Models |
| --- | --- | --- | --- | --- |
| Codex | 1.9 | ready | authenticated | 8 |
| Claude | 17.0 | ready | authenticated | 13 |

A run through `t3-provider-refresh.service` one minute later also gave
`ready` for both providers. The Claude value was 0.1 seconds because T3
used its five-minute probe cache.

T3 was not restarted and the host was not rebooted for this test.
The boot-time start of the unit is not yet tested.
These checks did not send a model prompt or test a live model conversation.

## Provider cache retry correction

Test date: 2026-10-13. Intel Core 2 Duo P8600, Ubuntu 24.04,
T3 0.0.45, Claude Code 2.1.295, and QEMU 8.2.2.
The fast MCP profile remained selected.

The startup refresh service failed after three Claude checks. The checks
were 45 seconds apart and each returned the initialization warning in
0.0 to 0.1 seconds. All retries ran within the five-minute probe cache.

A manual refresh after cache expiry returned `ready`, `authenticated`,
and 13 Claude models. The Claude status check took 30.8 seconds.
A separate read of the saved T3 status confirmed the same result.
These checks did not send a model prompt.

The local refresh helper now waits 310 seconds after the Claude
initialization warning. Other failures keep the 45-second wait.
The diagnostic session lasts 30 minutes, longer than the service limit.
The helper revokes the session when it finishes.
A manual service start finished with exit code 0. Both providers were
`ready`. The Claude check used the successful probe cache.
A second service start ran a fresh Claude check in 19.4 seconds. It also
returned `ready`, `authenticated`, and 13 models, and exited with code 0.
The host was not rebooted after the helper change.

Build checks, 20 project unit tests, and six local helper checks passed
with a standard system PATH. The helper checks cover cache expiry,
retry limits, other failures, and session duration. They use no real waits
or account credentials. Their files and the helper backup are under
`tools/diagnostics/` and are not stored in Git.
The local API integration test also passed. It checked streaming, shell
execution, search, tool results, and the `grep` and `find` shell functions.
This fixture does not prove a live account conversation.

## Provider refresh after the T3 0.1 update

Test date: 2026-10-24. Intel Core 2 Duo P8600, Ubuntu 24.04,
T3 0.1.1, Claude Code 2.1.308, and QEMU 8.2.2.

After the boots on 2026-10-21 and 2026-10-24, the refresh service failed
before it checked a provider. T3 rejected its WebSocket request with
`426 Upgrade Required` and `orchestration_protocol_incompatible`.
After the second boot, Codex showed `workspace routing discovery timed out`.

The helper now uses a WebSocket ticket and protocol version 2.
A manual service start finished with exit code 0. Codex returned `ready`,
`authenticated`, and 8 models in 5.0 seconds. Claude returned `ready`,
`authenticated`, and 13 models in 29.1 seconds. The one-minute load average
was 5.52, so the load wait stopped at its limit.
These checks did not send a model prompt.

The six local helper checks passed with a standard system PATH.
The host was not rebooted after this helper change.

## Provider status file and Telegram controls

Test date: 2026-10-24. Same host and versions as the T3 0.1 update test.

After a reboot at 01:58, T3's startup check returned
`Timed out after 25s while checking Claude account status`. The refresh
service ran without manual action. Codex returned `ready` in 1.9 seconds
and Claude returned `ready` in 18.8 seconds. The service exited with code 0.

An hourly `--check` run found both providers `ready` and did not refresh
them. It used 8.5 seconds of CPU time and wrote the status file.

The Telegram status bot was tested with the same systemd sandbox settings
as its service. It read the T3 unit state, the local server answer, the
tunnel process, and the status file. It started a user unit. Its 20 unit
tests passed with a standard system PATH. The Telegram buttons were not
yet pressed in the live chat. A T3 restart from Telegram is not yet tested.

