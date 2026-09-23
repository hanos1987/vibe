---
file: tests/t08_types.vibe
file-hash: 2a6d3cd5e86a8dbab5e2aa3dbe831802e1235a56
note-hash: c4fdc5dc36a563c3
---

# tests/t08_types.vibe

## What it is
Type layout: a struct that embeds a struct declared after it, `#` sizes, a self-referential linked-list node through a pointer, and a sum type holding a pointer.

## How to navigate it
`walk` sums a list; the entry function prints sizes and sums, then matches on `%Tree` and returns 2 to 4 on failure.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards that struct layout follows dependency order, not source order.

## Helpful notes
None.
