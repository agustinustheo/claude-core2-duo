# Claude CLI Core 2 Duo Emulator

Run the official Claude Code CLI on an older x86-64 Linux processor.
QEMU translates CPU instructions that the processor cannot execute.
The launcher does not change the Claude binary.

**Tested on an Intel Core 2 Duo P8600 with Ubuntu 24.04 and Claude Code 2.1.263.**
This CPU has no POPCNT, SSE4.2, AVX, or AVX2 support.
Other x86-64 processors with missing instructions might work. They are not yet tested.
A 32-bit Core Duo is not supported.

## Install

Use Ubuntu 24.04 x86-64 with Python 3.11 or later, Bash, `apt-get`, and `dpkg-deb`.
Other Linux distributions are not yet tested.

1. Download this repository, or clone it with Git.
2. Open a terminal in the repository directory.
3. Run these commands:

```bash
bash setup.sh
python3 update.py latest
./claude --version
./claude
```

The setup script downloads QEMU and ripgrep from your configured apt repositories.
The updater downloads Claude from Anthropic and checks its size and SHA-256 checksum.
It starts Claude through QEMU before it selects the new version.
These steps need internet access. They do not need root access.

Complete the normal Claude login. Claude uses your existing account and configuration.

## Use from another directory

Add this repository to the start of your PATH:

```bash
# Run this command from the repository directory.
export PATH="$(pwd):$PATH"
hash -r
claude --version
```

For future terminals, add the equivalent line to the end of `~/.bashrc`.
Use the full repository path in that line.
Check `type -a claude` if another installation still starts.

## Run outside a parent CPU limit

On Linux with a systemd user manager, use `./claude-scoped` to start Claude
in a separate `claude.slice`. This keeps a parent application's CPU quota from
slowing Claude startup. It does not change that parent application's quota.

```bash
./claude-scoped --version
./claude-scoped
```

The scope keeps the caller's directory, environment, arguments, and terminal.
For `--version` alone, it reports the selected installed release without starting
QEMU. The updater verifies and tests that release before selecting it. This fast
version report does not prove that the current runtime can start. Use the normal
`./claude --version` command to test the emulator.
It does not add a CPU quota. Claude and its child tools can use more CPU and
produce more heat. Limits on higher-level systemd slices still apply.
The normal `./claude` launcher continues to inherit the caller's limits.
A systemd user session is required. A failed scope creation stops the launcher.

## Update or select a version

```bash
./claude update latest
./claude update 2.1.263
```

The launcher disables automatic Claude updates. Use the commands above instead.
The updater keeps downloaded versions. The `previous` file records the last selected version.
To return to that version, supply its number to `update`.

## Limits

- Emulation is slower. One help command took 6.3 seconds and used about 214 MiB of memory.
- Interactive startup and a local API test passed. A live account conversation is not yet verified.
- Background sessions and other features that start Claude directly can bypass QEMU. These features are not yet verified.
- External tools must also support your CPU. Emulation does not extend to all child programs.

Claude still sends model requests to its normal service. This project does not run AI models locally.
QEMU is not a security boundary. Claude's normal permission checks remain in use.

See [test results](docs/testing.md), [known errors](docs/troubleshooting.md), and [contribution instructions](CONTRIBUTING.md).

## License

The project code uses the [MIT license](LICENSE).
Claude Code, QEMU, and ripgrep keep their own licenses. Their binaries are not in this repository.
This is an independent project. Anthropic does not maintain or endorse it.
