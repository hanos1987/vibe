---
file: tests/t31_containers.vibe
file-hash: 1ce377ecbc8d8b1aaa4ba70bc0a9da14cc1230df
note-hash: c1e45ee316088626
---

# tests/t31_containers.vibe

## What it is
Generic containers from heap.vibe: `%Vec<T>` of structs, floats and bytes, `%Map<V>`, `%IMap<V>`, and `%Buf` float and hex formatting, all through method syntax.

## How to navigate it
Everything is in the entry function, printing four lines.

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the generic container library.

## Helpful notes
A local variable named `ps` shadows the `ps` print function.
