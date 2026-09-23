---
file: vibelang/cli.py
file-hash: 044435ac33d4d6d47e917d03fafe2481e6698c50
note-hash: 2b46b3efaae4f936
---

# vibelang/cli.py

## What it is
The `vibec` command line: reads options, compiles a .vibe file and writes (or runs) the executable. The module docstring doubles as the `--help` text.

## How to navigate it
- `VERSION`: the release number.
- `stdlib_dir()`: finds the standard library folder.
- `main(argv)`: parses flags, calls `build`, then prints IR (`--ir`) or C (`--emit-c`), or picks a backend and writes/runs the binary. Start here.

## What it interacts with
Imports front.py (`build`, `CheckError`), parser.py (`ParseError`), lexer.py (`LexError`), codegen.py (`compile_program`), and cback.py (`emit_c`, `compile_program_c`, imported only when needed). Called by the `vibec` script and the `vibec` console entry in pyproject.toml; tests/fuzz.py and tests/fuzz4.py reuse `stdlib_dir`. Reads env var `VIBE_LIB`; also checks vibelang/stdlib, ../lib, /usr/lib/vibe/lib, /usr/local/lib/vibe/lib.

## Why it exists
It is the user-facing entry point of the compiler.

## Helpful notes
- Programs with C externs or 256-bit vectors switch to the C backend automatically, unless `--backend native` was given (then it errors).
- `--json` reuses the variable `out` for the error list.
- VERSION must be bumped here on release too.
