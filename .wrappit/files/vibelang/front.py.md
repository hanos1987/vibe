---
file: vibelang/front.py
file-hash: 75e8db2d1480cc5e25de85fc3f16093cc36b2740
note-hash: 174cd4d88de897aa
---

# vibelang/front.py

## What it is
The compiler front end: loads a program and its includes, resolves names and types, type-checks, and lowers (translates) everything to IR in one walk. Scalars go in vregs (virtual registers); structs and arrays are handled by address.

## How to navigate it
Start at `build()` at the bottom: `load`, then `collect`, then `lower_all`.
- Loading: `scan_generics`, `load` (includes, namespaces).
- Types: `resolve`, `inst_type` / `generic_call` (generic copies), `unify`.
- `collect`: declarations, constants, struct layouts, globals, signatures.
- Constants: `const_bytes`, `const_float`, `const_eval`.
- Lowering: `lower_fn`, `stmt`, `lower_match`, `lval`, `rval`, `lower_try`, intrinsics, `lower_format`, casts, `lower_bin`, calls.

## What it interacts with
Imports ast_.py, names.py, ir.py, parser.py (`parse`) and types.py. cli.py, tests/fuzz.py, tests/fuzz4.py, tools/ir.py and tools/disasm.py call `build`. `\fmt`/`\print` need heap.vibe from the stdlib.

## Why it exists
It is the bridge from syntax to the IR that the optimizer and both backends use.

## Helpful notes
- A program's declaration replaces a stdlib one of the same name; the library copy is renamed `std.name`.
- `names` is shadowed by a local in `collect`, hence the `MODNAMES` alias.
- `type_ready_fn` is unused.
