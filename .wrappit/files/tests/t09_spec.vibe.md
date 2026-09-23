---
file: tests/t09_spec.vibe
file-hash: 7467513debbe3e8a63ed28186a66bf1d74692056
note-hash: c933dc66a4babd46
---

# tests/t09_spec.vibe

## What it is
A tour of constructs the SPEC claims exist: a prime sieve over mmap memory, inferred `$ z =` types, else-if chains, array literals, pointer difference, short-circuit `&&`, and loop `*>` (continue) and `*<` (break).

## How to navigate it
`count` (sieve), `grade` (else-if) and `bump` (declared after use); the entry function prints five lines and returns 1 or 2 if short-circuiting fails.

## What it interacts with
Includes vibelang/stdlib/std.vibe (resolved from the stdlib directory). tests/run.py compiles and runs it, passing through any flags you give it (run it again with -O0 or --backend=c to test those modes), and compares stdout with the `; out:` header lines and the exit status with `; exit:` (0 if absent).

## Why it exists
It keeps the specification honest by testing its claims.

## Helpful notes
The sieve counts primes up to 1,000,000, so it is one of the slower tests.
