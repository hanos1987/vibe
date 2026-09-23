---
file: vibelang/regalloc.py
file-hash: 2520bb97dec8425f1a2bd8116882dc7fa067bc54
note-hash: 0ee6e285e06a99bd
---

# vibelang/regalloc.py

## What it is
Linear-scan register allocation: decides which vregs (the IR's unlimited numbered temporaries) get a real CPU register and which are "spilled" to a stack slot. Floats go in xmm (SSE) registers.

## How to navigate it
- Pools at the top: `GP_POOL`, `GP_CALLEE`, `XMM_POOL`; `CALL_LIKE`.
- `build_hints`: preferences that make moves disappear (share a register with the source, or use the ABI argument register).
- `build_blocks` and `liveness`: the control-flow graph and backward liveness fixpoint.
- `intervals`: first/last index where each vreg is live.
- `allocate(f)`: the main scan, weighting values by loop depth and evicting the least valuable when out of registers. Returns `{vreg: ('r',reg)|('x',xmm)|('m',)}` plus used callee-saved registers.
- `all_memory`: every vreg in memory (used for `-O0`).

## What it interacts with
Imports opt.py (`defs_of`, `uses_of`, `find_loops`) and x64.py (register numbers). codegen.py calls `allocate`/`all_memory` and uses `SMALL_COPY`; opt.py's `cse` imports `build_blocks`.

## Why it exists
Keeps hot values in registers so native code is fast.

## Helpful notes
- r10/r11, rax and xmm0-2 are never allocated; codegen.py uses them as scratch.
- A float live across a real call always goes to memory (SysV preserves no xmm).
- opt.py and this file import each other; `find_loops` is imported inside `allocate` to cope.
