---
file: examples/wc.vibe
file-hash: ed36650d2a998e5aa7354138179da1c32a7e75d5
note-hash: 0b006ff1e63f08db
---

# examples/wc.vibe

## What it is
An example program: a version of `wc` that prints lines, words and bytes for each file named on the command line.

## How to navigate it
`report` counts one file's contents and prints the tab-separated counts; the `@!` entry loops over arguments, reads each file with `fall`, and reports or prints an error.

## What it interacts with
It includes std.vibe (the standard library in vibelang/stdlib/std.vibe, which pulls in sys.vibe) for `fall`, `arg`, `argp` and printing; README.md points to it as the command-line tool example. No test script runs it; install.sh and packaging/mkdeb.sh copy examples/ into the installed share folder.

## Why it exists
It shows argv handling, file input and the heap in VIBE.

## Helpful notes
Exit status is 2 with no arguments, 1 if any file could not be read, otherwise 0. Words are split only on space, tab, newline and carriage return.
