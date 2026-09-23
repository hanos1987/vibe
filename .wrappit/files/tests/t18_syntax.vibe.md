---
file: tests/t18_syntax.vibe
file-hash: 4a4fe4b6edcb9aee0e3208da06134f385fbd44e9
note-hash: 3e378d0d173cad33
---

# tests/t18_syntax.vibe

## What it is
Syntax forms: bare (unbracketed) expressions, compound assignment, counted loops `* i 0 10`, `: {` else on its own line, `*<` lexing, and a statement that starts with a pointer cast.

## How to navigate it
Helper `f` plus the entry function, which prints six lines, one per feature.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards parser corner cases.

## Helpful notes
None.
