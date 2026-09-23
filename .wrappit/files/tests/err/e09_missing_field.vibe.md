---
file: tests/err/e09_missing_field.vibe
file-hash: 0ce1cfb5ddd40d4700d41e6479078c30708cd5b2
note-hash: ddc58132366f6689
---

# tests/err/e09_missing_field.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "missing field". It fails because a struct literal `%P{ a: 1 }` leaves out field `b`.

## How to navigate it
Line 1 is the `; err: missing field` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: a struct literal must give every field a value.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
