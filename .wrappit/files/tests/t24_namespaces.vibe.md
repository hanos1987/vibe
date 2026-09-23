---
file: tests/t24_namespaces.vibe
file-hash: b1e79a4d0c276aff1c30193b328bfa570c459162
note-hash: 6e4388ddebde20de
---

# tests/t24_namespaces.vibe

## What it is
Namespaced includes: `<<"lib/geom.vibe" g` puts that library's names under `g.` so they don't collide with std.vibe or the test's own `%Pt` and `area`.

## How to navigate it
The entry function uses `%g.Pt`, `g.max`, `g.area`, `g.calls`, `g.SCALE` and `@g.norm1` next to the test's own names, printing five lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe and tests/lib/geom.vibe (which itself includes tests/lib/geom_inner.vibe) (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards namespace scoping.

## Helpful notes
None.
