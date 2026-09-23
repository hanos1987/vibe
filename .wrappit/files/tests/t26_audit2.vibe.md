---
file: tests/t26_audit2.vibe
file-hash: 582c2ec3a08b298bfa9b6c26c290f33ed979cdf4
note-hash: 566fc551359e0201
---

# tests/t26_audit2.vibe

## What it is
Regressions from the second audit: `%=`, loop bounds that are read once even if the variable changes, float `+=`, while-style `*` with a cast condition, bool parameters, negative counted-loop ranges, the minimum s64, generic identity, and many local slots.

## How to navigate it
Helpers `two`, `wrap` and `many`; the entry function prints nine lines, one per case.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
Each line pins a bug found in the second audit.

## Helpful notes
`many` exists so the C backend's generated slot names reach `s8`, `s16`, which once clashed with type names.
