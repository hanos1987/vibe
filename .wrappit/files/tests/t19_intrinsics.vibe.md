---
file: tests/t19_intrinsics.vibe
file-hash: ce638ee66f4c513bbab4ec5c544f9e7d4d8a3c0e
note-hash: e6c994229f668e1d
---

# tests/t19_intrinsics.vibe

## What it is
Compiler intrinsics: `\sqrt`, `\bits`/`\fbits`, `\popcnt`, `\clz`, `\ctz`, `\bswap`, atomics `\cas` and `\xadd`, `\pause` and `\rdtsc`.

## How to navigate it
Everything is in the entry function, printing eight lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards that each intrinsic lowers correctly.

## Helpful notes
None.
