---
file: tests/err/e16_missing_return.vibe
file-hash: 6074d73412b9d2b4fbb49756eb44da7297ce61e0
note-hash: 88d155db11fc3a81
---

# tests/err/e16_missing_return.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "without returning". It fails because function `f` returns `s64` but only returns inside an `?` branch, so it can fall off the end.

## How to navigate it
Line 1 is the `; err: without returning` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: a function with a return type must return on every path.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
