---
file: tests/run.py
file-hash: 42a6a26a8a477887ae312cd254123a65c38cb91b
note-hash: 1579426181af4fa4
---

# tests/run.py

## What it is
The VIBE test runner. It compiles every tests/*.vibe program with ./vibec, runs it, and checks its output and exit code, then checks that every tests/err/*.vibe file fails to compile with the expected message.

## How to navigate it
`expectations()` reads the leading `; out:`, `; exit:` and `; err:` comment lines of a test file; `run_ok()` handles normal tests, `run_err()` handles error tests, and `main()` loops over both folders and prints PASS/FAIL plus a total.

## What it interacts with
Runs the `vibec` script at the repo root as a subprocess, reads every tests/*.vibe and tests/err/*.vibe file, and writes compiled binaries to temporary files that it deletes afterwards. It imports only the Python standard library.

## Why it exists
It is the project's regression suite: every compiler change must pass it in all three modes (default, `-O0`, `--backend=c`).

## Helpful notes
Run `python3 tests/run.py [flags]`; any argument starting with `-` is passed straight to vibec. Exit code is 1 if anything failed; each test binary gets a 60 second timeout, and empty stdout lines are ignored in the comparison.
