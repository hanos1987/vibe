---
file: tests/err/e17_literal_range.vibe
file-hash: 576d19d8df86ddcbe59f6819b2b19df104290bb0
note-hash: 98d4a466541c868b
---

# tests/err/e17_literal_range.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "does not fit". It fails because the literal 300 is stored in a local of type `u8`.

## How to navigate it
Line 1 is the `; err: does not fit` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: integer literals are range-checked against their target type at compile time.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
