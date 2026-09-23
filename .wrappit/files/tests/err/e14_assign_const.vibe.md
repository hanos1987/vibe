---
file: tests/err/e14_assign_const.vibe
file-hash: e6bfab98b0eda38a313084c9ce6f0335f81ce871
note-hash: cd69d2e2e13841b1
---

# tests/err/e14_assign_const.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "cannot be assigned". It fails because it assigns to `N`, a `$$` compile-time constant.

## How to navigate it
Line 1 is the `; err: cannot be assigned` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: `$$` constants are inlined values with no storage, so they can never be assigned.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
