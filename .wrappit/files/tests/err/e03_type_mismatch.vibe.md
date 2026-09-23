---
file: tests/err/e03_type_mismatch.vibe
file-hash: 014586dc6a2f57b7188ffb6e367e513bdc1c9111
note-hash: ec54a07f86ff4071
---

# tests/err/e03_type_mismatch.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "expected s64, got b". It fails because the boolean result of `(1 == 1)` is stored in an `s64` binding.

## How to navigate it
Line 1 is the `; err: expected s64, got b` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: there are no implicit conversions; a comparison gives a `b` (bool), never an integer.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
