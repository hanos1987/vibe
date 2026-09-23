---
file: bench/sieve.vibe
file-hash: 7f6a1e85528ef671522cd51bc09a88ae5d94de4c
note-hash: 72ef47b5032b6a3b
---

# bench/sieve.vibe

## What it is
A memory-bound benchmark: sieve of Eratosthenes up to 10,000,000, printing how many primes it found.

## How to navigate it
All in the `@!` entry: `mm` one byte per number, return 1 if that fails, then the marking loops and a final `pnl`.

## What it interacts with
Built and timed by bench/run.py, which compiles it with vibec (native and `--backend=c`) and compares it with bench/sieve.c, the matching C program written by bench/_mkc.py. It includes std.vibe (the standard library in vibelang/stdlib/std.vibe) for `pnl` and `mm`.

## Why it exists
It measures byte-array memory access against gcc.

## Helpful notes
It exits with status 1 if the mapping fails, which bench/run.py treats as a failure.
