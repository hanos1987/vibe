---
file: vibelang/lexer.py
file-hash: a47a96095bfbab04fbb14d23934a91a9013c3206
note-hash: 164c881e24678fc4
---

# vibelang/lexer.py

## What it is
The lexer: turns VIBE source text into a list of tokens (kind, value, line, column). Kinds are ID, INT, FLT, STR, P (punctuation/sigil), NL (newline) and EOF.

## How to navigate it
- `LexError`, `Tok`: the error and token classes.
- `PUNCT`: all sigils, longest first (order matters).
- `Lexer.run()`: the main loop (whitespace, `;` comments, newlines, numbers, identifiers, strings, byte literals, sigils).
- `lex_number`, `_escape`, `lex_string`, `lex_char`: helpers.
- `lex(src, filename)`: the entry point.

## What it interacts with
No local imports. parser.py calls `lex`; cli.py catches `LexError`.

## Why it exists
First stage of the compiler pipeline.

## Helpful notes
- Newline runs collapse into one NL token; statements end on NL.
- `*<` (break) and `*>` (continue) only lex as one token at the start of a line or after `{`; elsewhere they are `*` then `<`.
- A byte literal is a backtick then one character, with no closing mark.
- Non-ASCII letters are allowed in identifiers.
- `0o` with no digits raises a Python ValueError, not a LexError (0x and 0b check this).
