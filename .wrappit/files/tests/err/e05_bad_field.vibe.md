---
file: tests/err/e05_bad_field.vibe
file-hash: d324a0e78644d9e9028e4f8e09773784988f1e61
note-hash: 36f3b23b5d7cd81b
---

# tests/err/e05_bad_field.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "has no field". It fails because it reads `p.zz` from a struct `%P` that only has field `a`.

## How to navigate it
Line 1 is the `; err: has no field` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: field access is checked against the struct definition at compile time.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
