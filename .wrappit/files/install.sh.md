---
file: install.sh
file-hash: c547b41b9c74b5bd91b7c9e5227deb9e10775d29
note-hash: 73399d1662601c41
---

# install.sh

## What it is
The POSIX shell installer for Linux and macOS, run from a checkout or piped from `curl`.

## How to navigate it
- Header comment doubles as `--help` text; then `--prefix` option parsing (default `~/.local`).
- Checks for `python3`; uses the local checkout if `vibec` and `vibelang/` sit next to it, otherwise `git clone`s `VIBE_REPO`.
- Copies `vibelang/`, `vibec`, docs and `examples/` into `PREFIX/share/vibe`, writes a `PREFIX/bin/vibec` shim.
- Prints PATH advice, platform warnings and a hello-world to try.

## What it interacts with
- Copies vibec, the vibelang/ package, SPEC.md, README.md, LICENSE and examples/.
- External: python3, git, github.com/hanos1987/vibe.
- Linked from README.md and site/vibe.html; bundled by packaging/release.sh.

## Why it exists
One-line install on any Unix without pip or root.

## Helpful notes
Env vars `VIBE_REPO` and `VIBE_PREFIX` override the defaults. On macOS or non-x86_64 it installs but warns that output binaries need a Linux x86-64 host.
