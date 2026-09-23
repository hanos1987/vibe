---
file: tests/t17_ieee.vibe
file-hash: e032f322a3ae549c95b61069a684d934e8b02be7
note-hash: 9ebb63bf0c6a6b93
---

# tests/t17_ieee.vibe

## What it is
IEEE float rules: NaN compares, negative zero giving -inf, literals typed by context, string `==`/`!=`, and bool casts.

## How to navigate it
Everything is in the entry function, printing five lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards correct float comparisons and a few typing rules.

## Helpful notes
None.
