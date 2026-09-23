---
file: examples/par.vibe
file-hash: a3dd0a6d609b78083d387b2b8888b4085c0e6122
note-hash: 41455900d4227e5f
---

# examples/par.vibe

## What it is
An example program: counts primes below 400,000 in parallel by forking processes and collecting each count through a pipe.

## How to navigate it
`is_prime` and `count_range` do the work; the `@!` entry makes a pipe, forks `nproc` children (argument 1, default 4), sums their 8-byte results, waits for them, and prints the time.

## What it interacts with
It includes std.vibe (the standard library in vibelang/stdlib/std.vibe, which pulls in sys.vibe) for `fork`, `pip`, `wr`, `rd`, `waitpid` and `now_ns`. No test script runs it; install.sh and packaging/mkdeb.sh copy examples/ into the installed share folder.

## Why it exists
It shows how concurrency works with processes rather than threads in VIBE.

## Helpful notes
The last child takes any remainder of the range. Build and run as in the top comment: `vibec examples/par.vibe -o par && ./par 4`.
