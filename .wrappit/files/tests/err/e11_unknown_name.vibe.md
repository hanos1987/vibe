---
file: tests/err/e11_unknown_name.vibe
file-hash: b94d0ff4f2c6b7840335eb3dda9c04bfb5e57da4
note-hash: 37cc003201596a34
---

# tests/err/e11_unknown_name.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "unknown name". It fails because it returns `nope`, which is never declared.

## How to navigate it
Line 1 is the `; err: unknown name` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: every name must be declared before use; nothing is looked up at run time.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
