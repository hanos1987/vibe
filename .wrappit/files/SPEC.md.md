---
file: SPEC.md
file-hash: 05848dddc906ca2952f200fc955db67b4279e366
note-hash: 85843f1c22c1a7af
---

# SPEC.md

## What it is
The complete VIBE language reference, meant to be read once before writing any VIBE.

## How to navigate it
Intro with the three rules, then numbered sections: 1 Sigil reference, 2 Types, 3 Declarations, 4 Statements, 5 Expressions (operators, conversions, function pointers), 6 Pattern matching, 7 Talking to the machine (methods, results and `!`, formatting, SIMD, intrinsics, calling C), 8 Generics, 9 Namespaces, 10 Standard library, 11 Using the compiler, 12 Grammar, 13 Calling convention and layout, 14 What it does not have, 15 A complete program. Start at section 1.

## What it interacts with
- Describes the compiler in vibelang/ and the stdlib files (std.vibe, sys.vibe, heap.vibe, thread.vibe, math.vibe).
- Linked from README.md, site/vibe.html and install.ps1; shipped by install.sh and packaging/mkdeb.sh.

## Why it exists
The one authoritative definition of the language, for people and models.

## Helpful notes
The title says "v0.3" and section 14 says "What v0.2 does not have" (and lists no methods) while the package is 0.4.0 and section 7 documents methods; the headings lag the content.
