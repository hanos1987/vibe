---
file: tests/t37_simd.vibe
file-hash: d3c29e21cd80bfcae8e7cb95e7f7577c52159e96
note-hash: 9cffeef6d10c53ad
---

# tests/t37_simd.vibe

## What it is
SIMD vector types (f32x4, s32x4, f64x2): broadcast, operators, loads and stores through pointers, `\vsum`, `\vget`, `\vmin`, `\vmax`, `\vsqrt`, and vectors passed to and returned from functions.

## How to navigate it
`dot`, `scale` and `grind` helpers; the entry function prints eight lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe and vibelang/stdlib/math.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the vector types added in v0.4.0.

## Helpful notes
`grind` prints the `...` line itself, one dot per loop step.
