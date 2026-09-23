---
file: tests/err/e10_no_entry.vibe
file-hash: f966213435155496188c754d0425c85eae7a7efc
note-hash: dd7ad775bd21bfc3
---

# tests/err/e10_no_entry.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "no entry function". It fails because the program defines only `@ f` and no `@!` function.

## How to navigate it
Line 1 is the `; err: no entry function` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: every program needs exactly one `@!` entry point.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
