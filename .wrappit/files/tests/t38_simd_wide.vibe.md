---
file: tests/t38_simd_wide.vibe
file-hash: e898d733dc795ae880e1cd9f1786183bea5b65cb
note-hash: ed54d5c826bf71f0
---

# tests/t38_simd_wide.vibe

## What it is
256-bit vectors: f32x8, s32x8 and f64x4.

## How to navigate it
Everything is in the entry function, printing two lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the wide vector types.

## Helpful notes
Per its header, these are built through the C backend automatically, so a C compiler is needed.
