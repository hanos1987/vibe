---
file: tests/err/e23_vec_mismatch.vibe
file-hash: 92e4efe7e22ecfd03d9d96b29853cede9872c45b
note-hash: 077a99ba44d11379
---

# tests/err/e23_vec_mismatch.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "type mismatch". It fails because it adds an `f32x4` vector to an `f64x2` vector.

## How to navigate it
Line 1 is the `; err: type mismatch` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: SIMD vector arithmetic needs both operands to be the same vector type.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
