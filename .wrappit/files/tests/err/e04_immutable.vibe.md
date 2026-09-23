---
file: tests/err/e04_immutable.vibe
file-hash: ac30e4db92bb3ad6fde2c4012ec357c8359e45ea
note-hash: 78b0980e5588b13f
---

# tests/err/e04_immutable.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "immutable". It fails because a local declared with `$` (immutable) is reassigned with `x = 2`.

## How to navigate it
Line 1 is the `; err: immutable` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: only `$~` bindings are mutable; `$` bindings cannot be assigned after creation.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
