---
file: tests/t23_generics.vibe
file-hash: c8e6345f713e2e4430517ecc23796e3570b9004c
note-hash: eb62d6d2b833ef9e
---

# tests/t23_generics.vibe

## What it is
Generics: generic structs and sum types, generic functions with type inference and explicit `<f64>`, and `#` sizes of generic types.

## How to navigate it
Types `%Vec2<T>`, `%Opt<T>`, `%Pair<A,B>`; functions `gnew`, `gpush`, `glast`, `gmax`, `show`; the entry function prints six lines.

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards monomorphisation (one copy per concrete type).

## Helpful notes
None.
