---
file: tests/lib/geom_inner.vibe
file-hash: 59391237abfa8b48083e0a63597158433e63e57c
note-hash: 4306488cbcb9c066
---

# tests/lib/geom_inner.vibe

## What it is
A two-line VIBE helper file defining `norm1`, which returns `p.x + p.y` for a `%Pt`.

## How to navigate it
One function; nothing else.

## What it interacts with
It is included by tests/lib/geom.vibe, which supplies the `%Pt` struct it uses; that in turn is included by tests/t24_namespaces.vibe, run by tests/run.py. It includes nothing.

## Why it exists
It tests that a file included from inside a namespaced include lands in the same namespace (the test calls it as `g.norm1`).

## Helpful notes
It cannot compile on its own because `%Pt` is defined in geom.vibe, not here.
