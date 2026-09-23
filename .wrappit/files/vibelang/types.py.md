---
file: vibelang/types.py
file-hash: 1f24ffc52d1a631a9457a6d600b8c0e758f56420
note-hash: c302be17527fc536
---

# vibelang/types.py

## What it is
The compiler's internal type objects: integers (s8..u64), floats, bool `b`, void `v`, pointers, arrays, structs, sum types (tagged unions), function types and SIMD vectors. Each knows its size and alignment.

## How to navigate it
- `Type`: base class; equality compares the printed name; `is_scalar` / `is_agg` (aggregate: struct, array or sum).
- `IntT`, `FloatT`, `PtrT`, `ArrT`, `StructT` (with `layout` computing field offsets), `SumT` (8-byte tag, then payload), `FnT`, `VecT`.
- Singletons `VOID`, `BOOL`, `S8`..`F64`, then `PRIMS` (name to type, including vector names) and helpers `is_int`, `is_num`.

## What it interacts with
No local imports. front.py imports the singletons, `PRIMS` and the type classes.

## Why it exists
Type checking and memory layout both need one shared description of every type.

## Helpful notes
- Types compare by their string, so two different struct types with the same name would be equal.
- `VecT` has kind "vec", which is neither `is_scalar` nor `is_agg`.
- 128-bit vectors work on both backends; 256-bit ones need the C backend.
