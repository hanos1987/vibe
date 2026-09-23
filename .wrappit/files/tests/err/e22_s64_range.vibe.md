---
file: tests/err/e22_s64_range.vibe
file-hash: 1bb1efe1ebd026189a7becfbf86351d4497d2c3f
note-hash: 2fa00afbd5812848
---

# tests/err/e22_s64_range.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "does not fit". It fails because the literal 9223372036854775809 is assigned to an `s64`; that is larger than the biggest `s64` (9223372036854775807).

## How to navigate it
Line 1 is the `; err: does not fit` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: the literal range check works at the 64-bit edge too, so an out-of-range literal is not silently wrapped.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
