---
file: vibelang/ir.py
file-hash: 4715ba753c958a8b2f063a95ab9ca6f07266dd98
note-hash: 7803fae2a384a134
---

# vibelang/ir.py

## What it is
The data structures of VIBE's IR (intermediate representation: a simple list of instructions between the syntax tree and machine code). It uses vregs (virtual registers: unlimited numbered temporaries later mapped to real CPU registers) and explicit stack slots. Structs and arrays always live in memory, and their IR value is their address.

## How to navigate it
- `Slot`: one stack-frame memory area.
- `Ins`: one instruction: an `op` string plus up to five operands `a`..`e`.
- `Func`: one function; `vreg()`, `slot()`, `label()` and `emit()` are how the front end builds it; `dump()` prints it.
- `Program`: all functions, globals, read-only data (`add_ro` de-duplicates it), externs and the entry function.

## What it interacts with
No local imports. front.py builds it; opt.py imports `Ins` and `Func`; codegen.py and cback.py consume a `Program`. cli.py's `--ir` prints `Program.dump()`.

## Why it exists
One common format that the optimizer and both backends (native and C) work from.

## Helpful notes
- Operand meaning depends on the op; there is no schema here, so read how front.py emits an op to learn its operands.
- `wide_vectors` marks 256-bit vector use, which only the C backend supports.
