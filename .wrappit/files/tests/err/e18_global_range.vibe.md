---
file: tests/err/e18_global_range.vibe
file-hash: 39fbbfc160eeaa716398f738c9bc02bc2275f5e5
note-hash: 8a01127604ed88bf
---

# tests/err/e18_global_range.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "does not fit". It fails because the global `$ g u8 = 300` has an initializer too big for `u8`.

## How to navigate it
Line 1 is the `; err: does not fit` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: the literal range check also applies to global initializers.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
