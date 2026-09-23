---
file: tests/t07_const.vibe
file-hash: 0799256cf6571d8f6fecb6f1fd548b120ef85ae0
note-hash: 30bd351e8d04b2ca
---

# tests/t07_const.vibe

## What it is
Compile-time constants (`$$`), constants built from other constants, the size operator `#s64`, mutable globals (`$~`) and immutable globals (`$`).

## How to navigate it
One `tick` helper and the entry function, which prints 4096, 8 and 42 and returns 1 or 2 on failure.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards constant folding and global initialisation.

## Helpful notes
None.
