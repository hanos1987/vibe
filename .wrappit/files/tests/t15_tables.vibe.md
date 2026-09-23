---
file: tests/t15_tables.vibe
file-hash: 9adcea1c742caab4857d2f78f4d7aa29352e76ff
note-hash: e233509498aaa869
---

# tests/t15_tables.vibe

## What it is
Constant tables: global arrays and structs with initialisers, a constant used inside an array initialiser, and a partly initialised array whose missing entries are zero.

## How to navigate it
Globals `days`, `pts` and `origin` at the top; the entry function prints five lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards global data initialisers.

## Helpful notes
None.
