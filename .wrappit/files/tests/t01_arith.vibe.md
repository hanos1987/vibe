---
file: tests/t01_arith.vibe
file-hash: b41eba7e1adea71a7b34ba451decaff603f3e5a5
note-hash: 8a0f77d8007bfb9a
---

# tests/t01_arith.vibe

## What it is
Integer arithmetic: + - * / % shifts and bitwise ops, explicit grouping with brackets (VIBE has no precedence), and wrap-around of the sized types u8, s8, u16, u32, plus signed vs unsigned right shift.

## How to navigate it
One helper `chk(got, want)` and a flat list of `chk` calls in the entry function `@!`. A mismatch writes FAIL to stderr and exits with status 1; success returns 0.

## What it interacts with
No includes; it talks to the kernel directly through raw syscall intrinsics. tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards the most basic integer semantics, including C-style truncating division and remainder for negatives.

## Helpful notes
It prints nothing on success, so only the exit code matters (`; exit: 0`).
