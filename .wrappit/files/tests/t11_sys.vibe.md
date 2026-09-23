---
file: tests/t11_sys.vibe
file-hash: 90a75a1d753441a953f80ec23874796f74eb45b0
note-hash: b65b8cf9884daf2f
---

# tests/t11_sys.vibe

## What it is
The system library: argv, environment variables, number parsing, float printing and maths functions, heap `alloc`, `fork`/`waitpid`, and writing then reading back a file.

## How to navigate it
One `near` helper and `basefn`; the entry function goes through each category in order, printing a line per category and returning 1 to 14 on failure.

## What it interacts with
Includes vibelang/stdlib/std.vibe and vibelang/stdlib/math.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the stdlib parts that need the kernel.

## Helpful notes
It writes /tmp/vibe_t11.txt and needs PATH set in the environment.
