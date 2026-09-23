---
file: bench/_mkc.py
file-hash: afacb8678a033328b69274ccec1c8f936ef04c1f
note-hash: afd9d7eaa76fd117
---

# bench/_mkc.py

## What it is
A Python script that writes the C reference versions of the benchmarks: bench/fib.c, bench/sieve.c, bench/matmul.c and bench/mandel.c.

## How to navigate it
One dictionary `FILES` maps each C filename to its source text; the loop at the bottom writes them next to the script.

## What it interacts with
It is run by bench/run.py at the start of every benchmark run. Its C programs mirror bench/fib.vibe, bench/sieve.vibe, bench/matmul.vibe and bench/mandel.vibe. It imports only the Python standard library (os).

## Why it exists
Keeping the C sources in one generator keeps them matching the VIBE programs statement for statement, so the comparison measures code generation only.

## Helpful notes
Because it overwrites the .c files each run, edit the C here, not in the .c files.
