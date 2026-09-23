---
file: vibelang/codegen.py
file-hash: 7283997079089cf6857d02a8d1b56f164d7d14e4
note-hash: 2e716a09d2e0dadd
---

# vibelang/codegen.py

## What it is
The native backend: turns optimized IR into x86-64 machine code and then an ELF executable. Values the register allocator left in memory get a stack "home" and pass through scratch registers r10/r11 (xmm0-2 for floats).

## How to navigate it
- Start at `compile_program` (bottom) and `CodeGen.run`: prune, optimise, entry stub (saves the startup stack pointer, calls `@!`, exits with exit_group), each function, data, `link`.
- `gen_func`: frame layout (`layout_frame`), prologue, incoming arguments, then `gen_ins` per instruction.
- `gen_ins`: one branch per IR op; bigger ops in `gen_bin`, `gen_bini`, `gen_call`, `gen_cvt`, `gen_intr`, `gen_vec`.
- Helpers: `rd`/`wreg`/`done` (and float `rdf`/`wregf`/`donef`), `parallel_move`, `emit_branch`, `epilogue`.
- `link`: patches fixups and builds symbols.

## What it interacts with
Imports elf.py, opt.py, regalloc.py and x64.py. cli.py calls `compile_program`.

## Why it exists
The default way `vibec` makes binaries, needing only Python.

## Helpful notes
- `-O0` (`opt=False`) skips the optimizer and puts every value in memory.
- Functions with nothing on the stack are "frameless" (no rbp frame).
- `clone` inlines the thread-start code; `CLONE_FLAGS` matches cback.py's `vibe_clone`.
- 256-bit vectors are not handled here (only 128-bit).
