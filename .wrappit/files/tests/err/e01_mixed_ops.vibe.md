---
file: tests/err/e01_mixed_ops.vibe
file-hash: 524d4d94cc40d7204a837ab3164518bde10e5536
note-hash: 27a086fe6133914f
---

# tests/err/e01_mixed_ops.vibe

## What it is
A tiny VIBE program that must fail to compile with an error containing "no operator precedence". It fails because `^ (1 + 2 * 3)` mixes `+` and `*` without inner parentheses.

## How to navigate it
Line 1 is the `; err: no operator precedence` expectation comment; the rest is a few lines of code ending in the `@!` entry function.

## What it interacts with
Run by tests/run.py (the run_err check), which compiles it with vibec and passes only if compiling fails and the error text contains the `; err:` substring. It includes no other files.

## Why it exists
It proves the compiler enforces this rule: Rule 1 of SPEC.md: there is no operator precedence, so an operand of a binary operator may not itself be an unparenthesized binary expression of another operator.

## Helpful notes
The match is a case-insensitive substring of vibec's error output, so rewording that diagnostic in the compiler will break this test. Keep the program minimal so it triggers only this one error.
