---
file: tests/t10_fnptr.vibe
file-hash: f3de94606081e9c117054ff7ba81c54c02d5660f
note-hash: 02e1525889b3ba7e
---

# tests/t10_fnptr.vibe

## What it is
Function pointers: the `@(T,...)R` type, taking an address with `@name`, passing and returning function pointers, calling a call's result, pointers stored in structs, and comparing pointers.

## How to navigate it
`add`/`mul`/`sub`, a higher-order `fold`, and `pick` which returns a function; the entry function prints six lines and returns 1 or 2 on a bad comparison.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards indirect calls and function-pointer values.

## Helpful notes
None.
