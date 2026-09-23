---
file: tests/err/e20_struct_eq.vibe
file-hash: 9101301c498cdf837646b270041cece7e06eb96c
note-hash: f365feda44a97600
---

# tests/err/e20_struct_eq.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "cannot be applied". It fails because it compares two structs with `(p == p)`.

## How to navigate it
Line 1 is the `; err: cannot be applied` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: `==` is not defined on struct types.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
