---
file: vibelang/cback.py
file-hash: 607fd87cb0f36443baf2d2181efd06f784493dcd
note-hash: 73b644cff4ad1185
---

# vibelang/cback.py

## What it is
The C backend: prints the IR as freestanding C (one C variable per vreg) and compiles it with gcc or clang at -O3. The result is still a static binary with no libc, unless the program uses C externs.

## How to navigate it
- `PRELUDE`: C typedefs, unaligned-access structs, SIMD vector types, tiny `memcpy`/`memset`, `vibe_sys` (syscall), `vibe_clone` and float/bit helpers. `ENTRY`: the `_start` stub.
- `CGen.run`: globals, rodata, prototypes, externs, entry/`main`, then `func` per function; `ins` handles each IR op, with `vec`, `bin`, `cvt`.
- `find_cc`, `emit_c`, `compile_program_c`: pick a compiler, write a temp .c, run it, return the binary bytes.

## What it interacts with
Imports opt.py (`prune` only). cli.py uses `emit_c` and `compile_program_c`. Runs gcc/clang/cc; env vars `VIBE_CC` (compiler) and `VIBE_CFLAGS` (extra flags).

## Why it exists
`--backend=c` gets gcc/clang optimization quality from the same IR.

## Helpful notes
- It does not run the optimizer, so it only handles front-end IR ops.
- With externs it drops `-static`/`-nostdlib`, links `-l<lib>` and uses a C `main` that recovers argv's stack block.
- Wide (256-bit) vectors add `-mavx2`.
- Conversions mimic native hardware results (`vibe_f2i`).
