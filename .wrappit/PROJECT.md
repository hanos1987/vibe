# Project summary

## Purpose
VIBE is Ben's systems programming language with no natural-language keywords, only sigils. Its compiler, `vibec`, writes x86-64 Linux executables itself (no assembler, linker, libc or runtime), or goes through gcc/clang with `--backend=c` for C-level speed. The language is designed to remove the ambiguities that AI-generated code gets wrong.

## Key features
- Native backend writing ELF files directly; hello world is about 2 KB
- C backend (`--backend=c`) for gcc/clang -O3 parity, auto-used for C externs
- Generics, methods, `%Res`/`%Opt` with `!`, defer, namespaces, threads, FFI, SIMD vector types
- No operator precedence and no implicit conversions, by design
- Installs via script, pipx, signed APT repository, or .deb

## Tech stack
Python 3 with no dependencies (the compiler). Output: static Linux x86-64 executables. Optional gcc or clang for the C backend. Packaging: .deb, wheel, signed APT repo.

## How to run
`./vibec hello.vibe -o hello && ./hello`. Tests: `python3 tests/run.py`, which must also pass with `-O0` and `--backend=c`. Fuzzers: `tests/fuzz.py`, `tests/fuzz4.py`. Benchmarks: `python3 bench/run.py`.

## Development workflow
Read SPEC.md first; it is the whole language. Change the compiler, run all three test modes and the fuzzers. Release: bump VERSION in vibelang/cli.py, pyproject.toml and the packaging/site files; `packaging/release.sh`; `packaging/mkrepo.sh --sign <key>`; `gh release create`; sync packaging/apt to the benjiapps.com APT repo. The web page is site/vibe.html, built by `site/build_page.py`.

## Architecture overview
The compiler is the vibelang/ package, in pipeline order: lexer.py, parser.py (builds ast_.py nodes), names.py and types.py (resolution and checking), front.py (lowers to the IR in ir.py), opt.py (optimizer), then either the native path (regalloc.py, x64.py instruction encoding, codegen.py, elf.py) or cback.py (prints C). cli.py is the `vibec` command. vibelang/stdlib holds the standard library in VIBE. tests/ has one .vibe file per feature plus run.py. Start with SPEC.md, then cli.py and front.py.
