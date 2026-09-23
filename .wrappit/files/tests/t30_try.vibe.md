---
file: tests/t30_try.vibe
file-hash: d370232e60678d24e7e7a49e13f609dce35c09b5
note-hash: 1bb37698f95d7247
---

# tests/t30_try.vibe

## What it is
`%Res<T,E>` and `%Opt<T>` with the `!` operator, which returns early on Err/None.

## How to navigate it
`half`, `div`, `calc`, `find`, `after` and `show`; the entry function prints four lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards error propagation with `!`.

## Helpful notes
None.
