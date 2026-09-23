---
file: vibelang/stdlib/thread.vibe
file-hash: 6d16a75734eea187564d2a871894e90c0f0b3c7b
note-hash: 6924d8056331f7d4
---

# vibelang/stdlib/thread.vibe

## What it is
Real kernel threads for VIBE programs: `spawn` starts a function on its own 1 MB stack, `join` waits for it; plus a sleeping `%Lock` built on futexes (a kernel wait/wake primitive).

## How to navigate it
- `%Thread`, `spawn`: mmaps the stack, puts the handle at its base, protects the page above it (so an overflow traps), then calls the `\clone` intrinsic.
- `join`: futex-waits until the kernel zeroes `tid`, then unmaps the stack.
- `%Lock`: `lswap2`, `acquire` (spins 64 times, then sleeps), `release`.

## What it interacts with
Includes std.vibe (`<<"std.vibe"`) for `mm`/`mu`. Uses intrinsics `\clone`, `\cas`, `\xadd`, `\load`, `\store`, `\pause` implemented in codegen.py and cback.py. Programs include it themselves.

## Why it exists
Shared-memory parallelism without libc.

## Helpful notes
- Data other threads change outside a lock must use `\load`/`\store`.
- Programs with C externs should use libc threads instead.
- std.vibe's `lock`/`unlock` are cheaper for tiny critical sections.
