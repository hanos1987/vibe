---
file: tools/restyle.py
file-hash: d97c37add1fb9f3138357dbe1f81024e2569e2a3
note-hash: 700935838c449f0d
---

# tools/restyle.py

## What it is
Rewrites VIBE source files in place into the shorter "0.2 style": drops needless outer parentheses, turns `x = x + 1` into `x += 1`, and removes redundant `s64`/`f64` types on literal bindings.

## How to navigate it
- `depth0_ops` and `balanced`: small scanners that skip strings and track bracket depth.
- `strip_outer`: removes parentheses when at most one operator is at that level.
- `restyle_line`: the three regex rewrites; `main`: rewrites each file given.

## What it interacts with
Only the `.vibe` files passed on the command line; no repo imports. Mentioned in README.md.

## Why it exists
Moves older code to the economical style SPEC.md recommends ("Writing VIBE economically").

## Helpful notes
It edits files in place with no backup and is regex-based, not a compiler; recompile and run tests afterwards.
