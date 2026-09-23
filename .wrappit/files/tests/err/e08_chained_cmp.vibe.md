---
file: tests/err/e08_chained_cmp.vibe
file-hash: 3c403a8adc0b2b2f6927e23244555c43a415f457
note-hash: ee98698e03b4e238
---

# tests/err/e08_chained_cmp.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "does not chain". It fails because it writes `(1 < 2 < 3)`.

## How to navigate it
Line 1 is the `; err: does not chain` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: comparisons never chain; SPEC.md lists `a < b < c` as an error.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
