# Contribute

Keep changes small. Explain the fault and the new result.
Add a regression test when you fix a fault.

## File map

| File | Purpose |
| --- | --- |
| `claude` | Start QEMU and supply the search tool path |
| `setup.sh` | Download and check QEMU and ripgrep |
| `update.py` | Verify a Claude release and select it |
| `build.py` | Check Python and shell syntax |
| `tests/test_*.py` | Run checks without network access |
| `tests/integration.py` | Test real Claude with a local API service |
| `docs/` | Record hardware results and known errors |

Use the Python standard library. Do not add a framework for a small function.
Keep download, verification, and version selection separate.
A failed update must not select an unverified binary.
Keep the caller's working directory and arguments unchanged.

## Check a change

```bash
python3 build.py
python3 -m unittest discover -s tests
```

After a runtime change, also run `python3 tests/integration.py` with downloaded tools.
Optional pnpm commands are `pnpm run build`, `pnpm test`, and `pnpm run test:integration`.
Node and pnpm are not required to use this project.

Test from a normal terminal. Do not rely on an AI agent's private PATH.
Record the exact hardware when you claim CPU compatibility.

Use short sentences and direct instructions in documentation.
Follow ASD-STE100 writing rules. Keep technical names consistent.

Do not commit binaries, account files, local paths, or generated logs.
Contributions use the MIT license in `LICENSE`.
