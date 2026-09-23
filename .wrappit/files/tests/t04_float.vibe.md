---
file: tests/t04_float.vibe
file-hash: 0030cb2ff37054c456d104996c4358e479ad8712
note-hash: 0f57d0b2c05c3584
---

# tests/t04_float.vibe

## What it is
Floating point: f64 arithmetic, a struct of f64 fields passed by value, a hand-written Newton square root, f32 round trips, and int/float conversions.

## How to navigate it
`dot` and `sqrt` helpers, then the entry function prints 3, 314 and 1 and returns 1 to 6 on a failed check.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards float codegen and conversion casts.

## Helpful notes
It defines its own `sqrt` rather than using math.vibe.
