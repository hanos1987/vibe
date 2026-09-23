---
file: tests/t22_threads.vibe
file-hash: a2dbd07f787a214e8bcfe11d4cf6cc8c2b0d2f6d
note-hash: 00e20ab64ff42192
---

# tests/t22_threads.vibe

## What it is
Kernel threads, `\xadd` atomics, `lock`/`unlock`, and the thread-safe heap.

## How to navigate it
`worker` does the counting; the entry function spawns 4 threads, joins them and prints three totals.

## What it interacts with
Includes vibelang/stdlib/thread.vibe and vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards that concurrent code gets exact counts.

## Helpful notes
None.
