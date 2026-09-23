---
file: tests/t36_regalloc.vibe
file-hash: 528b05e9e0f64035136a563eddfbd37d14dd4c20
note-hash: 293ea798dfc46e2b
---

# tests/t36_regalloc.vibe

## What it is
Register pressure with shifts, division and syscalls, which need specific registers (rcx, rdx).

## How to navigate it
`mix` does the work; the entry function prints two lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards register allocation around instructions with fixed registers.

## Helpful notes
The `\1(1, "".p, 0)` inside the loop is a zero-length write syscall used only to clobber registers.
