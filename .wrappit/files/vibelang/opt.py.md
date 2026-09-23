---
file: vibelang/opt.py
file-hash: 42e6370af8e213965e5ed67c7930f8b8e91da354
note-hash: fe4b577a955e207f
---

# vibelang/opt.py

## What it is
The IR optimizer (IR: the compiler's instruction list between the syntax tree and machine code). Small passes that each preserve behaviour, so `-O0` gives a comparison run.

## How to navigate it
- Helpers: `defs_of`/`uses_of`/`replace_uses` (which vregs an instruction writes/reads), `def_counts`, `single_def_consts`.
- Passes: `fold_constants`, `fold_unary`, `copy_propagate`, `fold_addresses`, `use_immediates`, `fuse_index`, `fuse_branches`, `cse` (with `dominators`), `skip_narrow`, `coalesce_movs`, `dce`, `licm` (with `find_loops`), `strength_reduce`, `clean_labels`.
- `prune`: drops functions unreachable from `@!` (the entry).
- Inlining: `_inlinable`, `_splice`, `inline`.
- Start at `optimise(prog)` at the bottom: inline, then up to 3 rounds of all passes.

## What it interacts with
Imports ir.py (`Ins`, `Func`) and, inside `cse`, regalloc.py (`build_blocks`). codegen.py calls `optimise`/`prune` and the helpers; regalloc.py imports helpers; cback.py only uses `prune`.

## Why it exists
Makes native output fast while staying simple enough to verify.

## Helpful notes
- Passes create ops the front end never emits (`loadd`, `loadx`, `stored`, `storex`, `bini`, `cmpi`, `brc`, `fbrc`); only codegen.py understands them, so cback.py never runs `optimise`.
- Most passes only touch vregs defined exactly once.
- Inlining runs on raw front-end IR only (`_VFIELDS`).
