---
file: tests/t28_fconst.vibe
file-hash: 04f3d5cb73c485b6a59ed84f66f58c014dc8d6ef
note-hash: 29138bb5d35d93a2
---

# tests/t28_fconst.vibe

## What it is
Float constants: `$$` float constants, casts and arithmetic in global initialisers, and float global arrays.

## How to navigate it
Globals at the top; the entry function prints two lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards compile-time float evaluation.

## Helpful notes
None.
