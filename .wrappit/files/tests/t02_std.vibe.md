---
file: tests/t02_std.vibe
file-hash: 331ec0d61a711b6b80773e058e51ec27d501cca7
note-hash: 0b5be17ebee112de
---

# tests/t02_std.vibe

## What it is
Basic standard-library calls: printing strings, signed and hex numbers, heap memory through mmap, `set` (memset), and `min`/`max`.

## How to navigate it
A single entry function `@!` prints five expected lines; the mmap block returns 1 or 2 on failure.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It is the smoke test that the stdlib works without libc.

## Helpful notes
None.
