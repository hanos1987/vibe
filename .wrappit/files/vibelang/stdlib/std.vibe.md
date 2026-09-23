---
file: vibelang/stdlib/std.vibe
file-hash: 4bc4e404e2d5b11dc933e827371d120cd614f68f
note-hash: a9a4bc0b601f42f0
---

# vibelang/stdlib/std.vibe

## What it is
The core VIBE standard library, written in VIBE itself. It talks to the Linux kernel only through raw syscalls (`\N(...)`), with no libc: exit, byte I/O, printing strings and numbers, mmap memory, byte and string helpers, `%Res`/`%Opt`, and a spin lock.

## How to navigate it
Sections in order: process (`ex`), raw I/O (`wr`, `rd`), text output (`ps`, `pe`, `pc`, `nl`, `pn`, `pnl`, `px`), memory (`mm`, `mu`, `cp`, `set`), bytes (`ln`, `beq`, `seq`), integers (`abs`, `min`, `max`), the `%Res`/`%Opt` types, spin lock (`lock`, `unlock`), long-name aliases (`print`, `println`, `exit`...), and `%Str` view helpers (`ssub`, `sidx`, `sfind`, `strim`, `stok`, `sint`, `sfloat`, `uchars`).

## What it interacts with
Includes sys.vibe (`<<"sys.vibe"`), which includes this file back; the compiler loads each file once. Programs include it with `<<"std.vibe"`; found through cli.py's `stdlib_dir()` (or `VIBE_LIB`).

## Why it exists
Gives every program printing, memory and strings without a runtime.

## Helpful notes
- `ln` is string length, not a logarithm (math.vibe's log is `lg`).
- Unused functions are pruned, so the aliases cost nothing.
- A program's own function with the same name replaces the library one.
