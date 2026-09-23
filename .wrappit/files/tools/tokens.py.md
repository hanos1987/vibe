---
file: tools/tokens.py
file-hash: 196fa7403db2aeae2702ea1c90af7a30c72cf2ea
note-hash: 218a6b8bdab4d658
---

# tools/tokens.py

## What it is
Measures how many tokens (o200k tokenizer) VIBE programs cost compared with their C equivalents.

## How to navigate it
`strip()` removes comments and blank lines per language; the module-level loop builds `.vibe`/`.c` pairs (arguments or `bench/*.vibe` with matching `.c`), prints each ratio and a total.

## What it interacts with
- Reads bench/*.vibe and the bench/*.c files that bench/run.py generates.
- External: the `tiktoken` Python package.
- Its result is quoted in README.md (0.99x).

## Why it exists
Backs the claim that VIBE is cheap for a model to write.

## Helpful notes
Run bench/run.py first, or there are no `.c` files to pair. Exits with a message if tiktoken is missing.
