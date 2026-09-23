---
file: tests/err/e13_immutable_global.vibe
file-hash: 598ab653867dd24c8f58c30fd9654edbd048554a
note-hash: b8bf171b2824660d
---

# tests/err/e13_immutable_global.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "immutable". It fails because the global `$ cap` (immutable) is assigned `cap = 20` inside the entry function.

## How to navigate it
Line 1 is the `; err: immutable` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: the immutability of `$` applies to globals too, not just locals.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
