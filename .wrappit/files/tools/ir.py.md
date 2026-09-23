---
file: tools/ir.py
file-hash: c74173b7936a7c3cd1dab380505b777d6f57f95f
note-hash: 8c1a47782cd9061d
---

# tools/ir.py

## What it is
A developer tool that prints the compiler's IR for a program, or one function: `python3 tools/ir.py prog.vibe px [--raw]`.

## How to navigate it
One `main()`: `build` the program with the stdlib include dir, run `optimise` unless `--raw`, then print `f.dump()` for each matching function.

## What it interacts with
Imports vibelang/front.py (`build`), vibelang/opt.py (`optimise`) and vibelang/cli.py (`stdlib_dir`).

## Why it exists
To see what the optimiser did (or the raw lowering) for a specific function.

## Helpful notes
With no function name it dumps every function, including the stdlib ones.
