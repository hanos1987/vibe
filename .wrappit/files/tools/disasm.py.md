---
file: tools/disasm.py
file-hash: 390e2f53b658007a4b80dbe1d549abb28cd7ca9a
note-hash: 6cf80cf506ab03b8
---

# tools/disasm.py

## What it is
A developer tool that disassembles the native machine code emitted for one VIBE function: `python3 tools/disasm.py prog.vibe fib`.

## How to navigate it
One `main()`: build the program, run `CodeGen`, find function label offsets. With no function name it lists offsets; otherwise it slices that function's bytes to a temp file and prints `objdump` output plus byte and instruction counts.

## What it interacts with
- Imports vibelang/front.py (`build`), vibelang/codegen.py (`CodeGen`) and vibelang/cli.py (`stdlib_dir`).
- External: objdump.

## Why it exists
To inspect native-backend code quality per function; VIBE binaries have no section headers, so objdump can't do it directly.

## Helpful notes
Pass `-O0` anywhere in the arguments to see unoptimised code.
