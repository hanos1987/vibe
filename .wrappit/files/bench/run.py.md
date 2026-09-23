---
file: bench/run.py
file-hash: 05cc0d8dd1a2ede93fdbd41a804b583771bc4a1e
note-hash: 1d72218ac77bed46
---

# bench/run.py

## What it is
The benchmark driver: it builds each benchmark as VIBE native, VIBE `--backend=c`, and gcc -O0/-O2/-O3, times each, and prints a table.

## How to navigate it
`BENCHES` lists the programs and `REPS` the repeat count; `timeit` takes the least user CPU time over REPS runs; `main` builds, times and prints.

## What it interacts with
It runs bench/_mkc.py first, then compiles bench/fib.vibe, bench/sieve.vibe, bench/matmul.vibe, bench/mandel.vibe with the repo's vibec, and their .c twins with gcc. Run it as `python3 bench/run.py`.

## Why it exists
It gives the speed numbers for VIBE versus C and checks every build prints the same answer, so a fast but wrong result cannot pass.

## Helpful notes
It needs gcc installed. Binaries are written into bench/ as <name>.<0-4>.bin. Any differing output is marked MISMATCH in the table rather than stopping the run.
