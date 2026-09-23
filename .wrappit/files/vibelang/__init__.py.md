---
file: vibelang/__init__.py
file-hash: e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
note-hash: 79e346cca61f3eab
---

# vibelang/__init__.py

## What it is
An empty file. Its only job is to mark the vibelang/ folder as a Python package.

## How to navigate it
Nothing to read: the file has no code.

## What it interacts with
No imports. Its presence lets other code write `from vibelang.cli import main` (the `vibec` launcher script and the `vibec` console entry in pyproject.toml) and `from vibelang.front import build` (tests/fuzz.py, tests/fuzz4.py, tools/ir.py, tools/disasm.py), and lets the modules inside import each other with `from . import ...`.

## Why it exists
Python needs it so the compiler's modules can be imported as one package, both from a checkout and from an installed copy.

## Helpful notes
None. Nothing is re-exported here, so callers import from the specific module (cli.py, front.py, ...).
