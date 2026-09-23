---
file: vibelang/names.py
file-hash: 747b64dcbc5b94ba382f926cba2ae3acf86dc1b7
note-hash: 2a5d02e1b8c7a0d9
---

# vibelang/names.py

## What it is
Support for namespaced includes: `<<"geom.vibe" g` makes that file's top-level names usable only as `g.name`. It does this by renaming names inside the included files' syntax trees before type checking.

## How to navigate it
- `declared(decls)`: collects the top-level function, struct, sum and global names (skipping the entry `@!`).
- `prefix(decls, ns, names)`: renames those names to `ns.name` at their declarations and every use. Inner helpers: `rename` (one node), `walk` (expressions/types), `block` (statements, tracking local variables in scope).

## What it interacts with
Imports ast_.py. Used by front.py: in `load` for namespaced includes, and in `collect` to hide a stdlib declaration under `std.` when the program declares the same name.

## Why it exists
So the rest of the compiler only ever sees plain, already-unique names and needs no namespace logic of its own.

## Helpful notes
- A local variable, parameter or match binding with the same name hides the file-level name only after it is bound and only inside its block; `block` implements this rule.
- It mutates the AST nodes in place.
