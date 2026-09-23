---
file: tests/t35_audit3.vibe
file-hash: 2b1eab49ec58f1f777f22240b99f8200816c49a1
note-hash: ceaa2171ab8f119d
---

# tests/t35_audit3.vibe

## What it is
Regressions from the third audit: u64 to f32 rounding, an index expression evaluated once in a method call, `\fmt` of large and special floats, `!` inside a larger expression, and `!` on a comparison.

## How to navigate it
Helpers `idx`, `inc`, `half` and `f`; the entry function prints four lines.

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
Each line pins a bug found in the third audit.

## Helpful notes
None.
