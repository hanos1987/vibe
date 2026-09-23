---
file: tests/t13_regress2.vibe
file-hash: 3c73e357b3a29fcc281753d4ddc163edc1d41a3e
note-hash: 3db9185e99b222d4
---

# tests/t13_regress2.vibe

## What it is
Register allocation around calls: a parameter must survive a call that is the first instruction of its function; also `ln` on a string pointer.

## How to navigate it
`noop` and `keep` helpers; the entry function prints 42 and 12.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards a register-allocator bug where an early call clobbered a parameter.

## Helpful notes
None.
