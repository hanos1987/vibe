---
file: bench/fib.vibe
file-hash: 87d6bae35852c18658442279335adf3ad195882f
note-hash: 174f15d1fc643440
---

# bench/fib.vibe

## What it is
A benchmark program: naive recursive Fibonacci of 35, printed with `pnl`.

## How to navigate it
A header comment, the recursive `fib` function, and the `@!` entry that prints `fib(35)`.

## What it interacts with
Built and timed by bench/run.py, which compiles it with vibec (native and `--backend=c`) and compares it with bench/fib.c, the matching C program written by bench/_mkc.py. It includes std.vibe (the standard library in vibelang/stdlib/std.vibe) for `pnl`.

## Why it exists
It measures function-call and recursion overhead of VIBE's code generation against gcc.

## Helpful notes
The C twin must stay statement-for-statement the same, or the timing comparison stops being fair; bench/run.py also checks both print the same number.
