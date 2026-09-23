---
file: tests/t06_regress.vibe
file-hash: eb4685bba3db45d0553e26f8369b2bdab4fd444a
note-hash: 33004aece95fa35e
---

# tests/t06_regress.vibe

## What it is
Optimiser and register-allocator regressions: hex printing with `px`, loops, and deeply nested if/else inside a loop.

## How to navigate it
`sum_to` and `mixed` helpers; the entry function prints five lines and returns 1 if `mixed(3)` is wrong.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
Its header records a real bug: a value hoisted out of a loop (LICM) had its register reused, because a fused compare-and-branch was not treated as a block end, which broke `px`.

## Helpful notes
None.
