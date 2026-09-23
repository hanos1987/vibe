---
file: tests/err/e19_dup_noinit.vibe
file-hash: c195de79e5da2762327a3d335e2eb560ad370c51
note-hash: bca7e4a347631782
---

# tests/err/e19_dup_noinit.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "already bound". It fails because it declares `a`, then redeclares `$~ a s64` (with no initializer) in the same scope.

## How to navigate it
Line 1 is the `; err: already bound` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: a name cannot be bound twice in one scope, even by a zero-initialised `$~` declaration.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
