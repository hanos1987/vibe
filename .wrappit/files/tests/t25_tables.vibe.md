---
file: tests/t25_tables.vibe
file-hash: 601a08130a7c15dc3358281ea5c50b5396306e1b
note-hash: b5eba9b18f7abb1e
---

# tests/t25_tables.vibe

## What it is
Global tables of `%Str` strings and of structs holding function pointers, plus string comparison and a global string.

## How to navigate it
Helpers `dbl` and `neg`, globals `days`, `cmds` and `msg`; the entry function prints three lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards global initialisers for strings and function pointers.

## Helpful notes
None.
