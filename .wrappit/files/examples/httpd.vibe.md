---
file: examples/httpd.vibe
file-hash: 215e15d3398e369f242fb1a6e1079076d48cc396
note-hash: c4f951502dd0c297
---

# examples/httpd.vibe

## What it is
An example program: a tiny HTTP server with no libc, answering every request with a fixed HTML page.

## How to navigate it
The top comment shows how to build and run it. `serve` reads a request and writes a fixed header and body via raw syscalls `\0` and `\1`; the `@!` entry parses the port and optional request limit, binds with `srv`, and loops on `acc`.

## What it interacts with
It includes std.vibe (the standard library in vibelang/stdlib/std.vibe, which pulls in sys.vibe) for `srv`, `acc`, `fc`, `nat`, `arg` and printing. No test script runs it; install.sh and packaging/mkdeb.sh copy examples/ into the installed share folder.

## Why it exists
It shows VIBE can do networking directly through syscalls.

## Helpful notes
Usage: `./httpd 8080` serves forever; `./httpd 8080 3` serves three requests and exits. The request is read but never parsed.
