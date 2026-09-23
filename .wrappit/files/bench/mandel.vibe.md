---
file: bench/mandel.vibe
file-hash: f000c15564045e31c0b5ab50ee65cef71b7a11dc
note-hash: aa268efa68f94305
---

# bench/mandel.vibe

## What it is
A floating-point benchmark: a 900x900 Mandelbrot set with at most 100 iterations per pixel, printing the total iteration count.

## How to navigate it
Everything is in the `@!` entry: two nested `*` range loops over pixels and an inner `*` while-loop for the iteration.

## What it interacts with
Built and timed by bench/run.py, which compiles it with vibec (native and `--backend=c`) and compares it with bench/mandel.c, the matching C program written by bench/_mkc.py. It includes std.vibe (the standard library in vibelang/stdlib/std.vibe) for `pnl`.

## Why it exists
It measures f64 arithmetic and tight-loop code quality against gcc.

## Helpful notes
Note the explicit parentheses everywhere (VIBE has no precedence) and the explicit `f64(px)` casts (no implicit conversions); the C version in bench/_mkc.py mirrors each step.
