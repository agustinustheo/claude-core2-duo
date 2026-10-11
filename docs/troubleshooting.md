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

### `Could not verify Claude authentication status from initialization result`

T3 0.0.45 shows this warning when its capability probe returns no result.
The probe has a 25-second deadline. T3 hides the error, so this warning alone
does not prove a timeout or a login fault.
T3 caches the result for five minutes, including a failed result.
A conversation can work while the provider status still shows this warning.

Use an explicit provider status refresh after the five-minute probe cache
expires. A workspace refresh can leave the original provider status in place.
Do not sign out only because of this warning.
The probe disables user hooks and MCP connections, but still loads plugins
and commands. CPU load during startup can make the probe miss its deadline.
A longer probe deadline and a shorter cache time for failed probes require
a change in T3. They cannot be set in this launcher.

## T3 hides Codex models after a provider timeout

T3 0.0.45 gives the Codex provider check 10 seconds. This check starts the
app server and reads the account, skills, models, and usage limits.
If the check times out, T3 publishes an error with an empty model list.
An existing Codex conversation can still work.

`Timed out while checking Codex app-server provider status` does not mean
that the executable is missing. A successful version check alone does not
test all provider checks. Retry the provider check after machine load falls.
Do not change the binary path only because of this timeout.

## T3 keeps an old provider warning

Check the provider's `checkedAt` time. A new thread or a workspace refresh
does not always run a new authentication probe. In T3 0.0.45, a refresh with
both `instanceId` and `cwd` updates workspace skills and commands. It can
keep the original provider status, including a startup error.

An explicit `server.refreshProviders` request with `instanceId` and without
`cwd` runs the provider status check. This request needs an authenticated
T3 client. It does not send a model prompt or stop an existing conversation.
Refresh one provider at a time on this two-core host.

The five-minute Claude capability cache and the displayed provider status
are separate. Waiting for the cache to expire does not refresh the display.
Do not remove MCP servers or sign out only to clear an old warning.

### Refresh the provider status after each T3 start

On the tested host, a user service runs this refresh after each T3 start.
The script is `~/.local/bin/t3-refresh-providers`. The unit is
`~/.config/systemd/user/t3-provider-refresh.service`. They are not part of
this repository.

The script waits for the T3 server. Then it waits until 60 seconds after
the T3 start and until the one-minute load average is 1.5 or less. The load
wait stops after five minutes. Then the script refreshes each enabled
provider, one at a time. It tries a provider again two times if the status
is not `ready`. It uses a 20-minute T3 session and revokes it at the end.

To refresh now, run `t3-refresh-providers --now`. To see the last result:

```bash
journalctl --user -u t3-provider-refresh.service -n 20
```

To stop the automatic refresh:

```bash
systemctl --user disable t3-provider-refresh.service
```

The refresh does not make T3 startup faster. A new thread can still fail
before the refresh completes. The T3 deadlines and CPU quota do not change.

## Existing T3 threads work, but new sessions are slow

An existing session can keep its provider process. A new session must start
that process and load its settings, plugins, hooks, and MCP servers.
A session restored after a server restart must also start a new process.

On the tested host, T3 and Codex share a one-core CPU quota. Git checks and
other child processes use the same quota. Claude uses a separate slice,
but QEMU still needs CPU time. Simultaneous startup work can delay the
provider status checks past their deadlines.

Check the service quota and current memory use:

```bash
systemctl --user show t3code.service -p CPUQuotaPerSecUSec -p CPUWeight
free -h
```

Review plugins and MCP servers that load at each session start. A tool with
`needs-auth` status is not ready. Remove unused tools through the application
that manages them. Do not delete synchronized plugin files by hand.
For the scoped launcher, the local `fast` profile skips automatic MCP
connections. See the startup profile instructions in the README.
An MCP server supplied with `--mcp-config` can still connect. T3 supplies its
own server this way. To restore automatic connections for future sessions,
write `full` to `tools/startup-profile`.
If a hook reports `python: command not found`, its command must use an
available Python interpreter. That error does not prove a startup timeout.

For T3, a longer probe deadline, background retries, and retention of known
models after a failed check can improve startup reliability. These changes
need a T3 change. This launcher cannot set those probe options.
Do not use Claude's `--bare` mode to fix an OAuth account: that mode does
not read OAuth credentials.

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
