---
file: tests/t27_u64float.vibe
file-hash: 29dce122fed8cfbad4d3fb173f24437c0aa5e4d7
note-hash: 8fdecaccc097ec1f
---

# tests/t27_u64float.vibe

## What it is
Conversions between u64 and floats for values at or above 2^63.

## How to navigate it
Everything is in the entry function, printing three lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe and vibelang/stdlib/math.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards unsigned-to-float and float-to-unsigned conversion edge cases.

## Helpful notes
None.
