---
file: vibelang/stdlib/sys.vibe
file-hash: a75515fbb8d472abbaccf99ec8ec94982ef6e527
note-hash: 9cf1b31ce454b87a
---

# vibelang/stdlib/sys.vibe

## What it is
The system part of the VIBE standard library, in VIBE: program arguments and environment, a bump arena allocator, number parsing, float printing, files, time, processes and TCP sockets, all through raw syscalls.

## How to navigate it
In order: `argc`, `argp`, `arg`, `envp`, `env` (read from `__sp`, the stack pointer at startup); arena `alloc`; `nat` (decimal parse); `pf`/`pfl` (print a float); file flags and `fo`, `fc`, `fsz`, `fall` (read a whole file); `now_ns`, `nap`; `fork`, `pid`, `waitpid`, `exec`, `pip`, `dup2`; sockets `hton16`, `srv` (bind+listen), `acc`.

## What it interacts with
Includes std.vibe (`<<"std.vibe"`), which includes this file back. Uses std's `mm`, `ln`, `beq`, `pc`, `pn`, `nl`. `__sp` is a global the compiler's entry stub fills (codegen.py / cback.py). heap.vibe's `new` uses `alloc`.

## Why it exists
OS services for programs without libc.

## Helpful notes
- `alloc` never frees; arenas are 1 MB mmap blocks. Use heap.vibe for `del`.
- `pf` goes through s64, so huge values overflow; heap.vibe's `bpf` handles them.
- `nat` duplicates std.vibe's `sint`.
