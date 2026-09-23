---
file: tests/t21_defer.vibe
file-hash: 3358ba32eb165037f5c9347dd53a1f0892b8e790
note-hash: 4b8598896d8b690d
---

# tests/t21_defer.vibe

## What it is
`~` deferred statements: running in reverse order at scope exit, on normal return, on early return, and on `*<` break inside a loop.

## How to navigate it
`f` (two defers and a deferred assignment), `early` (return path) and a loop in the entry function; six expected lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards defer ordering on every exit path.

## Helpful notes
None.
