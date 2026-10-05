# Known errors

## `claude --version` shows the old version

**Cause:** The shell selects another Claude installation, or keeps its old command path.

From this repository, run:

```bash
./claude --version
export PATH="$(pwd):$PATH"
hash -r
type -a claude
claude --version
```

Put the repository PATH entry after Node version manager setup in `~/.bashrc`.
Do not replace an unrelated executable.

## `Please install ripgrep (rg)`

**Cause:** An early launcher depended on `rg` from the developer's private PATH.
That directory was not present in the user's terminal.

The current setup installs a local copy. The launcher also supplies it to child processes.
Run:

```bash
bash setup.sh
./tools/ripgrep/usr/bin/rg --version
./claude --version
```

The tests now use a standard system PATH.

## `E: Unable to locate package rg`

**Cause:** `rg` is the command name. The Ubuntu package name is `ripgrep`.

The local setup above is sufficient. For an optional system installation, use:

```bash
sudo apt install ripgrep
```

## `Illegal instruction` or exit code 132

**Cause found on the P8600:** The native Claude binary executed `POPCNT` during startup.
The CPU cannot execute that instruction.

Start `./claude`, not a file in `downloads/`.
The launcher starts the binary through QEMU.

If the launcher still fails, record the CPU model, OS, Claude version, and full error.
A new release can use an instruction or system call that the emulator cannot process.

## `grep` or `find` stops with `Illegal instruction` in the Bash tool

**Cause:** Claude's shell snapshot replaces `grep` and `find` with functions.
They start `CLAUDE_CODE_EXECPATH` as `ugrep` or `bfs`. Claude sets that variable
to the native binary for each command, so the functions do not use QEMU.

The launcher sets `CLAUDE_CODE_SHELL_PREFIX` to `claude-shell`. That script
points `CLAUDE_CODE_EXECPATH` to the launcher. The launcher finds the fixed
`ugrep` and `bfs` arguments and starts those modes through QEMU.
Claude also uses this prefix for command hooks and stdio MCP servers.

Start a new Claude session after an update. A running session keeps its old
environment. If you set your own `CLAUDE_CODE_SHELL_PREFIX`, the launcher
does not replace it, and this fault can return. `/usr/bin/grep` and
`/usr/bin/find` always use the system tools.

Do not add `Grep` to `--allowedTools` for this fault. That also stops the
functions, but it changes the tool set and permission rules.

## Search fails although Claude starts

Claude's internal search can start its own executable without QEMU.
The launcher sets `USE_BUILTIN_RIPGREP=0` and uses local ripgrep instead.
Run `bash setup.sh` if that copy is missing.
Do not start the downloaded Claude binary directly.

## An option is unknown

Use the exact option name. For example, `--dangerously-skip-permissions` ends with `s`.
That option disables permission checks. It is not required for CPU compatibility.
Use `./claude --help` to see the available options.

## The repository directory moved

PATH entries and symbolic links can still point to the old directory.
Update those paths, then run `hash -r`.
The launcher finds its files relative to its own location.

## A download or checksum check fails

The updater does not select the new version until verification succeeds.
Check the connection and retry the same update command.
Do not disable the checksum check.

If setup reports a missing shared library, install the matching distribution dependency.
The local setup checks each tool before it copies the files into place.

## T3 cannot verify authentication on a CPU-limited host

T3 can time out before QEMU finishes startup. The tested T3 release has a
four-second version deadline and a 25-second initialization deadline.
A successful `claude auth status` does not prove that initialization meets them.

Use the optional `claude-scoped` launcher with a systemd user manager.
Set T3's Claude binary path to that launcher. Changing PATH alone does not fix
an existing absolute binary path in T3 settings.

The scoped launcher reports the selected installed version without emulation
for `--version` alone. Real sessions run in `claude.slice`, outside the parent
application's CPU quota. This can increase host CPU use and temperature.
It does not remove limits on higher-level systemd slices. A separate CPU weight
can prioritize the slice during contention. No weight is required by the script.

Initialization still depends on machine load and QEMU. If it exceeds T3's
remaining deadline, the timeout needs an upstream or separately tested change.
The launcher does not fake authentication or initialization results.

## QEMU uses much CPU

**Cause:** QEMU emulates each instruction. It must also emulate the JIT compilers
in Claude's JavaScript engine, and then translate the code that they make.

The launcher sets `BUN_JSC_useDFGJIT=0`. This disables the DFG JIT compiler.
It also sets `BUN_GC_TIMER_INTERVAL=30000`. The periodic GC then runs every 30 seconds.
Memory pressure still starts GC at other times.
On the P8600, these settings decreased CPU time for one local conversation by about 29%.
An idle session used less than 1% of one core with and without this setting.
High CPU use during startup, responses, and tool calls is expected.

Do not disable all JIT compilers. That did not decrease CPU time.
Do not set `BUN_JSC_numberOfGCMarkers=1`. That almost doubled CPU time.
Do not decrease the JIT thresholds. That increased CPU time and memory use.
A different QEMU `-cpu` model did not change CPU time.
QEMU 10.2, 11.0, and 11.1 used slightly more CPU time than QEMU 8.2.2.
GC heap growth and allocator settings did not change CPU time.

If a long session becomes slower, start it with `BUN_JSC_useDFGJIT=1 ./claude`.
If memory use increases too much, start it with `BUN_GC_TIMER_INTERVAL=1000 ./claude`.
