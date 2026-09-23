---
file: tests/t05_mem.vibe
file-hash: e98ce269dcf8e82cdaec016423a3ee29b6f882e0
note-hash: b76bdec2eaea2682
---

# tests/t05_mem.vibe

## What it is
Memory and aggregates: recursion (fib, fact), structs returned by value, nested structs, pointer writes with `p'`, globals and global arrays, local arrays of structs, and pointer-to-struct field access.

## How to navigate it
Helpers `fib`, `fact`, `mkbox`, `bump`, `sum_arr`; the entry function prints four numbers and then returns 1 to 11 for each failed check.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards memory layout, pointers and by-value aggregates.

## Helpful notes
None.
