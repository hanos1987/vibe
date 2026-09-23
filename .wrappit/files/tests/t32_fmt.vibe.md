---
file: tests/t32_fmt.vibe
file-hash: 1bb4b4b77ca012aee2f6731e2620eae7f8222648
note-hash: f086a23d5d4d1828
---

# tests/t32_fmt.vibe

## What it is
String formatting intrinsics `\fmt`, `\print` and `\eprint`, with `{}`, `{c}`, `{x}`, `{.2}` and `{{` escapes, across integer, float, string, char, bool and pointer arguments.

## How to navigate it
Everything is in the entry function, printing three lines to stdout (one line goes to stderr and is not checked).

## What it interacts with
Includes vibelang/stdlib/heap.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the formatting intrinsics.

## Helpful notes
None.
