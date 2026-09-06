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
