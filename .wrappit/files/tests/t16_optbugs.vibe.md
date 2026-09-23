---
file: tests/t16_optbugs.vibe
file-hash: 682a3083614e50ac621edf211cec2672a570ceb7
note-hash: f94eaa943a74663d
---

# tests/t16_optbugs.vibe

## What it is
Optimiser regressions: a reassigned parameter used as a loop counter, `*>` (continue) inside a loop, and a narrow (s32) negative literal.

## How to navigate it
`count` and `skip` helpers; the entry function prints four lines.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
Each case is a past optimiser bug named in the header comment.

## Helpful notes
None.
