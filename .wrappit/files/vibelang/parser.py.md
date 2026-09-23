---
file: vibelang/parser.py
file-hash: f4a8816ca42ace22dcef3ffe3322599ea1c764c6
note-hash: 5deddc68c3defd19
---

# vibelang/parser.py

## What it is
The parser: turns tokens into AST nodes. Each declaration or statement form is decided by its first sigil. There is no operator precedence: mixing different operators without parentheses is a parse error.

## How to navigate it
- Token helpers on `Parser` (`at`, `eat`, `expect`, `end_stmt`).
- `parse_unit` / `parse_decl`: top level (`<<` include, `@<` extern, `@` function, `%|` sum, `%` struct, `$` global).
- Types: `parse_type`, `parse_tparams`, `parse_targs`.
- `parse_stmt`: all statements (`$` let, `~` defer, `^` return, `?` if, `*` loop, `??` match, assignment).
- Expressions: `parse_expr`, `parse_unary`, `parse_postfix`, `parse_primary`.
- `parse(src, filename, generics)`: entry point.

## What it interacts with
Imports lexer.py (`lex`, `Tok`) and ast_.py. front.py calls `parse`; cli.py catches `ParseError`.

## Why it exists
Second stage of the pipeline, after the lexer.

## Helpful notes
- The parser must be told the generic function names up front (front.py scans for them); only then does `name<` start type arguments.
- `star_is_cast` decides whether a line-leading `*` is a loop or a pointer-cast store.
- A `>>` closing nested type arguments is split by mutating the token.
- `Tok` is imported but unused; `if op in CMP_OPS: pass` does nothing.
