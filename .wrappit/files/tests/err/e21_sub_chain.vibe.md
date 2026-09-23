---
file: tests/err/e21_sub_chain.vibe
file-hash: a35eb0b909e24a50b5e65aa5e4ab98b7b08fe3ef
note-hash: 1d016ec454311f7d
---

# tests/err/e21_sub_chain.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "does not chain". It fails because it writes `(10 - 3 - 2)`.

## How to navigate it
Line 1 is the `; err: does not chain` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: only `+ * & | ^ && ||` may chain; subtraction (like `/ % << >>`) does not, because grouping would change the answer.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
