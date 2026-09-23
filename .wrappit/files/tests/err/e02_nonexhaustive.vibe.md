---
file: tests/err/e02_nonexhaustive.vibe
file-hash: b4a7905121d3886cf97b412b635bdd002bd16473
note-hash: 64b3bea419b3e3da
---

# tests/err/e02_nonexhaustive.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "not exhaustive". It fails because a `??` match on the sum type `%R` handles only the `|A` case and leaves out `|B`.

## How to navigate it
Line 1 is the `; err: not exhaustive` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: a match over a sum type must cover every variant.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
