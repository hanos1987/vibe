---
file: tests/err/e15_addr_of_const.vibe
file-hash: ea72ba51a4b643155a5a52f9024bbcb3d1b75ee8
note-hash: 9a932e6a231006db
---

# tests/err/e15_addr_of_const.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "has no address". It fails because it takes `&N` of a `$$` constant.

## How to navigate it
Line 1 is the `; err: has no address` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: `$$` constants have no address (SPEC.md: they are inlined at every use).

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
