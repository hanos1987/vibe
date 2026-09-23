---
file: tests/t12_heap.vibe
file-hash: 0ae3af6ed99e5757fbe3964cb73713c1d8f9083b
note-hash: f6bffea653840535
---

# tests/t12_heap.vibe

## What it is
heap.vibe: allocator block reuse, a large allocation, the `%Buf` string builder, the `%Vec<s64>` vector, and the `%Map<s64>` string map with set/get/delete.

## How to navigate it
Everything is in the entry function, in that order, with one printed line per check.

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the heap library and its containers.

## Helpful notes
It has no `; exit:` line, so the runner expects 0.
