---
file: tests/t14_manyargs.vibe
file-hash: 9fbd5d7f1d96e89454ffa53e6a918f8d29ec63fc
note-hash: e464c79e657424e2
---

# tests/t14_manyargs.vibe

## What it is
Calls with more arguments than there are argument registers: 8 and 10 integers, 9 floats plus an integer, and an 8-argument function pointer.

## How to navigate it
Helpers `dig`, `sum10` and `fs`; the entry function prints four lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards stack-passed arguments in the calling convention.

## Helpful notes
None.
