---
file: tests/err/e06_arity.vibe
file-hash: a43ee3755fc185de7b2104dd4043d65fcc5b43fe
note-hash: 3af2edc7f42055b2
---

# tests/err/e06_arity.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "takes 2 argument". It fails because function `f` takes two parameters but is called as `f(1)`.

## How to navigate it
Line 1 is the `; err: takes 2 argument` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: calls must pass exactly the number of arguments the function declares.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
