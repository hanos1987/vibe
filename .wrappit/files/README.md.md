---
file: README.md
file-hash: 493b3f04c7f70113c9329b06d2da74efe22ec02d
note-hash: 920efb79f7e08dac
---

# README.md

## What it is
The front page of the VIBE repo: what the language is, how to install it, and what it can do.

## How to navigate it
Sections in order: intro with hello world, Install (platform table, signed APT setup), Why it looks like this (three rules), What is in the language, What you can build with it, Layout (repo map), Running the tests, Benchmarks, Status.

## What it interacts with
- Links SPEC.md; refers to install.sh, install.ps1, packaging/release.sh, packaging/mkrepo.sh, tools/restyle.py, tools/tokens.py, bench/run.py, tests/run.py, examples/ and vibelang/.
- External: GitHub releases, benjiapps.com/vibe/apt.
- Used as the package description by pyproject.toml; shipped by install.sh and packaging/mkdeb.sh.

## Why it exists
The first thing a visitor or installer reads.

## Helpful notes
Install links hard-code 0.4.0. The Status section still says "v0.3" and lists methods as absent, although the feature table lists methods; it looks out of date.
