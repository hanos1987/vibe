---
file: tests/fuzz4.py
file-hash: 23f34e7979bb7826e3bd7ab857c58b248317191c
note-hash: cdfd401a410c47e8
---

# tests/fuzz4.py

## What it is
A richer differential fuzzer that compares three builds of each random program: optimised native, unoptimised native (-O0), and the C backend. It covers floats, structs, sum types, generics, intrinsics, globals, compound assignment and counted loops.

## How to navigate it
`PRE` is a fixed prelude of types and helper functions every program starts with; class `G` generates expressions and statements; `helpers()` makes five random functions with up to 12 parameters; `gen(seed)` builds the program; `run(path, mode)` compiles with mode o1, o0 or c.

## What it interacts with
Imports `build` from vibelang/front.py, `compile_program` from vibelang/codegen.py, `compile_program_c` from vibelang/cback.py and `stdlib_dir` from vibelang/cli.py; generated programs include std.vibe. It writes into ./fz4/ or the given output directory.

## Why it exists
It checks that the optimiser and the C backend agree with the plain native backend on a wider feature set than tests/fuzz.py.

## Helpful notes
Usage: `python3 tests/fuzz4.py A B [outdir]`. Set NOC=1 to skip the C backend (needs no gcc/clang then); set VIBEROOT to use another checkout. Failing seeds are kept on disk and printed.
