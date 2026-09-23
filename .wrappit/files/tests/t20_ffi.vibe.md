---
file: tests/t20_ffi.vibe
file-hash: 4dc2ea8b6fb668e547d52dc2647db2b037ff0f2a
note-hash: b196b8005e733686
---

# tests/t20_ffi.vibe

## What it is
Calling C through `@<` declarations: variadic `printf`, `strlen`, `fflush`, libm `pow`, and a renamed import (`cabs = abs`).

## How to navigate it
The `@<` declarations at the top, then the entry function prints five lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the foreign function interface.

## Helpful notes
It needs a C compiler and libc/libm; per PROJECT.md, programs with C externs go through the C backend automatically.
