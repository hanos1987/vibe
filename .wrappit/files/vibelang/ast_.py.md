---
file: vibelang/ast_.py
file-hash: 67f8b844e6190d4ba47dd545ca01481798a2a59e
note-hash: 9f4e3c74f3e15be5
---

# vibelang/ast_.py

## What it is
The node classes of the AST (abstract syntax tree: the program as a tree of objects, built by the parser). Every node records its line and column so error messages can point at the exact spot.

## How to navigate it
- `Node`: the base class (line, col, `ty`, source file, is-stdlib flag).
- `_mk(name, fields)`: a small factory that makes each node class with the listed fields.
- Then the node lists in order: type expressions (`TName`, `TPtr`, `TArr`, `TNamed`, `TFn`), declarations (`FnDecl`, `StructDecl`, `SumDecl`, `ExternDecl`, `GlobalDecl`, `Include`), statements (`Let`, `Assign`, `If`, `While`, `For`, `Defer`, `Match`...), patterns (`PVar`, `PWild`) and expressions (`Bin`, `Call`, `Try`, `Cast`, `StructLit`...). Comments show the VIBE sigil for many.

## What it interacts with
No local imports. parser.py builds these nodes; names.py rewrites them; front.py type-checks and lowers them.

## Why it exists
It is the shared data shape between the parser and the rest of the compiler.

## Helpful notes
- Nodes use `__slots__`, so you cannot add ad-hoc attributes beyond the listed fields plus `line`, `col`, `ty`, `_file`, `_std`.
- Constructor arguments are positional in field order; missing ones default to None.
