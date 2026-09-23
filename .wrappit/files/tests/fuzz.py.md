---
file: tests/fuzz.py
file-hash: eeeda73062cd941a8f32c9e55c8c59199edc6fbb
note-hash: 32b4bec3dd4d9c7f
---

# tests/fuzz.py

## What it is
A differential fuzzer: it generates random integer-only VIBE programs and checks that each one gives the same exit code and output with the optimiser on and off.

## How to navigate it
Class `G` builds random expressions, conditions, variables, if/else blocks and loops; `helpers()` makes four random helper functions `g0`..`g3`; `gen(seed)` assembles a full program; `run()` compiles and executes it; the bottom loop walks the seed range.

## What it interacts with
Imports `build` from vibelang/front.py, `compile_program` from vibelang/codegen.py and `stdlib_dir` from vibelang/cli.py; generated programs include std.vibe. It writes programs and binaries into ./fz/ in the current directory.

## Why it exists
It catches optimiser miscompiles that hand-written tests miss, by using the unoptimised build as the reference answer.

## Helpful notes
Usage: `python3 tests/fuzz.py A B` for seeds A to B-1, run from a scratch directory. Passing seeds are deleted; mismatching or crashing seeds are left in fz/ and printed; set VIBEROOT to point at another checkout.
