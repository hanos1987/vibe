---
file: tests/t33_lock.vibe
file-hash: bd753e32615d61ef368bcb869f99cdb20fde5ab0
note-hash: 99a5881eb202459f
---

# tests/t33_lock.vibe

## What it is
The futex-backed `%Lock` under contention from 8 threads.

## How to navigate it
`worker` does acquire/increment/release; the entry function spawns 8 threads, joins them and prints 800000.

## What it interacts with
Includes vibelang/stdlib/thread.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the lock and, per its header, the guard page below each thread stack.

## Helpful notes
None.
