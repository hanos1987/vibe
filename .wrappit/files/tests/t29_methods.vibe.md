---
file: tests/t29_methods.vibe
file-hash: 145a32ad166914e33214490aadcfa508668b78a8
note-hash: be25ec133f41c755
---

# tests/t29_methods.vibe

## What it is
Method syntax: `x.f(a)` calls `f(x, a)` or `f(&x, a)`, on generic structs, plain structs, pointers and plain integers.

## How to navigate it
Types `%Vec2<T>` and `%Pt`; functions `gpush`, `glast`, `sum`, `scale`, `dbl`; the entry function prints four lines and returns 0 only if `five.dbl() == 10`.

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards method-call lowering.

## Helpful notes
None.
