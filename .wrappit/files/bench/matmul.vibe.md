---
file: bench/matmul.vibe
file-hash: 99b8961589483adb28ea7fe8f7a06decde41fa34
note-hash: ff250d3c84b67f7a
---

# bench/matmul.vibe

## What it is
A benchmark: 400x400 integer matrix multiply, printing the sum of the result matrix.

## How to navigate it
All in the `@!` entry: allocate three matrices with `mm`, fill a and b, the triple loop computing c, then sum c.

## What it interacts with
Built and timed by bench/run.py, which compiles it with vibec (native and `--backend=c`) and compares it with bench/matmul.c, the matching C program written by bench/_mkc.py. It includes std.vibe (the standard library in vibelang/stdlib/std.vibe) for `pnl` and `mm` (memory mapping).

## Why it exists
It measures nested loops and array indexing against gcc.

## Helpful notes
Memory comes from `mm` (an mmap wrapper), matching the C version's mmap calls, so allocation is identical on both sides.
