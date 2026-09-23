---
file: tests/err/e07_width_mix.vibe
file-hash: ccf7bcb809ae251c798c0cafadc60b66bb1587c8
note-hash: cdd82b1754b2143c
---

# tests/err/e07_width_mix.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "never converts silently". It fails because it adds an `s64` and an `s32`.

## How to navigate it
Line 1 is the `; err: never converts silently` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: integers of different widths never convert silently; the programmer must cast.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
