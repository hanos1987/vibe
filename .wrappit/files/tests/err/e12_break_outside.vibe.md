---
file: tests/err/e12_break_outside.vibe
file-hash: 1387f21807ce4a314496414cdc3194cb0fc20457
note-hash: 885f1b6a2f1a2c86
---

# tests/err/e12_break_outside.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "outside a loop". It fails because a `*<` (break) appears directly in the function body with no loop around it.

## How to navigate it
Line 1 is the `; err: outside a loop` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: break is only legal inside a loop.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
