---
file: vibelang/elf.py
file-hash: f37e6d0a2d44abe88c245d032a86f877c5310f81
note-hash: 3c7fbc4dec8442c4
---

# vibelang/elf.py

## What it is
Writes a minimal static ELF64 executable (ELF is the Linux binary file format). The output has no interpreter, no dynamic linking and no libc: two loadable segments, read+execute (code and read-only data) and read+write (data, plus zeroed bss).

## How to navigate it
- `plan_layout(code_len, rodata_len)`: the addresses code, rodata and data will get, so jumps and data references can be patched before the file is built.
- `build_elf(...)`: ELF header, the two program headers, then the bytes.
- `symtab(...)`: optional section headers and a function symbol table appended at the end, for gdb/perf/objdump only.

## What it interacts with
No local imports (only Python's `struct`). codegen.py calls `plan_layout` and `build_elf` in `CodeGen.link`.

## Why it exists
The last step of the native backend: it turns machine code into a runnable file without a linker.

## Helpful notes
- `plan_layout` repeats `build_elf`'s offset arithmetic; change one and you must change the other.
- The data segment's address is the text base + 0x200000 + its file offset.
- `symtab` patches the already-written ELF header (shoff, shnum=7, shstrndx=6) in place.
