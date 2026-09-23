---
file: tests/err/e24_vec_op.vibe
file-hash: 7444c1fa1570d613aefc488336a12850525fefa6
note-hash: 6006675b258978ca
---

# tests/err/e24_vec_op.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "not defined on". It fails because it applies `%` (remainder) to two `f32x4` vectors.

## How to navigate it
Line 1 is the `; err: not defined on` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: not every operator is defined on SIMD vector types; `%` on float vectors is rejected.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
