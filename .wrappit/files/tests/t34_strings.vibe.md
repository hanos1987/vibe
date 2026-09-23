---
file: tests/t34_strings.vibe
file-hash: 58bd077e0f4def5e8cfc5c2450d1ae0bea76a3a6
note-hash: 86025e862bcfc491
---

# tests/t34_strings.vibe

## What it is
String helpers in std.vibe: `sidx`, `sfind`, `strim`, `ssub`, `sstarts`, `sends`, `stok`, `sint`, `sfloat`, `uchars` and `ln` on UTF-8 text.

## How to navigate it
Everything is in the entry function, printing five lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the string library.

## Helpful notes
It contains non-ASCII text (é and Japanese characters) to test UTF-8 counting.
