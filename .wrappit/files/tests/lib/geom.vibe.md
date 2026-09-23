---
file: tests/lib/geom.vibe
file-hash: 65ac6ba9f4e214e2392becde383bd29cbd6fe030
note-hash: 4739d31b6ae2439a
---

# tests/lib/geom.vibe

## What it is
A small VIBE library used as test data for namespaced includes. It defines a struct `%Pt`, a constant `SCALE`, a mutable global counter `calls`, and functions `max` and `area`.

## How to navigate it
The first comment explains its purpose; then the include of geom_inner.vibe, the declarations, and the two functions.

## What it interacts with
It includes tests/lib/geom_inner.vibe (for `norm1`). It is included by tests/t24_namespaces.vibe as `<<"lib/geom.vibe" g`, and so is exercised through tests/run.py.

## Why it exists
Its names (`max`, `area`, `%Pt`) deliberately collide with std.vibe and with names in the test, to prove that a namespaced include keeps them apart.

## Helpful notes
It is not a test by itself: tests/run.py only runs .vibe files directly in tests/ and tests/err/. Inside `area`, a local named `max` shadows the function `max`, which is also part of what it checks.
