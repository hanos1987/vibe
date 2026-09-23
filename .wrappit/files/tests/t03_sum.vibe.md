---
file: tests/t03_sum.vibe
file-hash: f0c1df94c8e9291060c3c4b822c650665aa46097
note-hash: b0a2e2b1be40a1eb
---

# tests/t03_sum.vibe

## What it is
Sum types (tagged unions, `%|`) with payloads, a struct payload, construction like `%Res|Ok(...)`, and exhaustive matching with `??`.

## How to navigate it
`divide` returns a `%Res`, `show` matches on it and prints `ok`/`err`/`none`; `area` matches on `%Shape`. The entry function checks `area` results and returns 1 to 3 on failure.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It guards sum-type layout, construction and matching.

## Helpful notes
None.
