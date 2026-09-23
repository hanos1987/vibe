---
file: vibec
file-hash: 3b1a2b1fa30f6e432578b30b57a09bfae2252afd
note-hash: 0cd3c1abbda44666
---

# vibec

## What it is
The compiler's launcher script, used when running straight from a checkout (`./vibec hello.vibe -o hello`).

## How to navigate it
Thirteen lines: add the repo folder to `sys.path`, import `main` from `vibelang.cli`, and exit with its return code.

## What it interacts with
- Imports `vibelang/cli.py` (`main`), which does all the real work.
- Copied and wrapped by install.sh and packaging/mkdeb.sh; packaging/release.sh puts it in the source tarball.
- Installed pip/pipx copies use the `vibec` console script in pyproject.toml instead.

## Why it exists
So the compiler runs from a clone with no install step.

## Helpful notes
Needs `python3` on the PATH (shebang `/usr/bin/env python3`). It has no logic of its own; change behaviour in vibelang/cli.py.
