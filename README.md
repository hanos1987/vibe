# VIBE

A systems language with no natural-language keywords, compiled straight to
x86-64 machine code. `vibec` writes the ELF bytes itself — there is no
assembler, no linker, no C library and no runtime anywhere in the pipeline.

```
@! () s64 {
  $ s %Str = "hello from VIBE\n"
  \1(1, s.p, s.n)
  ^ 0
}
```

```
$ vibec hello.vibe -o hello && ./hello
hello from VIBE
```

Read [SPEC.md](SPEC.md) — it is the complete language, written to be read
once before writing any VIBE.

## Install

`vibec` is Python 3 with no dependencies, so it installs anywhere. The
executables it *emits* are static Linux x86-64: on Windows run them under
WSL, on macOS run them in a container or VM.

| Platform | Command |
|---|---|
| Debian / Ubuntu | `sudo apt install vibe` (after adding the repo, below) |
| Any Linux, macOS | `curl -fsSL https://raw.githubusercontent.com/hanos1987/vibe/master/install.sh \| sh` |
| Any, with pip | `pipx install vibe-lang` |
| Windows | `irm https://raw.githubusercontent.com/hanos1987/vibe/master/install.ps1 \| iex` |
| From source | `git clone https://github.com/hanos1987/vibe && cd vibe && ./install.sh` |

APT repository:

```sh
curl -fsSL https://benjiapps.com/vibe/apt/vibe.gpg \
  | sudo tee /usr/share/keyrings/vibe.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/vibe.gpg] https://benjiapps.com/vibe/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/vibe.list
sudo apt update && sudo apt install vibe
```

Or download the `.deb` directly and `sudo apt install ./vibe_0.1.0_all.deb`.

Build every release artifact yourself with `packaging/release.sh`, and the
APT repository with `packaging/mkrepo.sh --sign <key>`.

## Why it looks like this

Three rules, each removing an ambiguity that generated code gets wrong:

1. **No operator precedence.** `(1 + 2 * 3)` is rejected; write
   `(1 + (2 * 3))`. An expression means what its shape says.
2. **No implicit conversions.** `s64 + s32` is rejected. Nothing changes
   representation silently.
3. **One statement per line.** No semicolons, no line joining.

Plus: matches must be exhaustive, mutation requires `$~`, and every
construct is a single sigil, so nothing depends on knowing English.

## What you can build with it

Every category below is covered by a program in this repository that runs.

| Category | Proof | What it needs |
|---|---|---|
| Games, terminal UI | `examples/snake.vibe` | raw mode, non-blocking input, frame timing |
| Command line tools | `examples/wc.vibe` | argv, file i/o, heap |
| Network services | `examples/httpd.vibe` | sockets, bind/listen/accept |
| Parallel compute | `examples/par.vibe` | fork, pipes, wait |
| Numerics | `vibelang/stdlib/math.vibe` | f64, sqrt/exp/log/trig |
| Systems, embedded | the compiler's own output | syscalls, inline machine code |

`examples/wc.vibe` produces byte-identical output to GNU `wc`.
`examples/httpd.vibe` serves real HTTP to `curl`.

Not covered: threads (concurrency is by `fork`), and anything needing a GUI
toolkit, which would mean speaking X11 or Wayland over a socket yourself.

## Layout

```
vibec                the compiler entry point
vibelang/
  lexer.py           sigil tokeniser
  parser.py          recursive descent, enforces the no-precedence rule
  front.py           type checking and lowering, in one walk
  ir.py              linear IR with virtual registers
  opt.py             folding, DCE, LICM, branch fusion, addressing modes
  regalloc.py        liveness dataflow and linear-scan allocation
  x64.py             instruction encoder
  codegen.py         IR to machine code
  elf.py             static ELF64 writer
  stdlib/            std.vibe, sys.vibe, math.vibe — all written in VIBE
examples/            snake, wc, httpd, par
tests/               behavioural and diagnostic tests
bench/               benchmarks against gcc
packaging/           .deb, APT repo, release artifacts
tools/               IR and disassembly dumps
```

## Running the tests

```
python3 tests/run.py          # optimised
python3 tests/run.py -O0      # every value in memory, no allocation
```

Both paths must agree; `-O0` exists as an independent oracle for the
optimiser.

## Benchmarks

Identical programs, best of three, outputs verified equal.

| bench | VIBE | gcc -O0 | gcc -O2 | vs -O0 | vs -O2 |
|---|---|---|---|---|---|
| fib(35) | 0.044s | 0.059s | 0.018s | 1.37x | 0.41x |
| sieve 10M | 0.029s | 0.068s | 0.024s | 2.34x | 0.84x |
| matmul 400 | 0.063s | 0.131s | 0.039s | 2.07x | 0.62x |
| mandel 900² | 0.061s | 0.135s | 0.041s | 2.20x | 0.66x |

Roughly 2x faster than `gcc -O0` and within about 1.5x of `gcc -O2`, from a
compiler with a dozen optimisation passes rather than several hundred. The
remaining gap is mostly inlining and induction-variable strength reduction.

A VIBE binary is 2 KB where the equivalent static C binary is 785 KB,
because there is no libc to carry.

```
python3 bench/run.py
```

## Status

v0.1. Types, control flow, structs, tagged sums with exhaustive matching,
pointers, arrays, floats, function pointers, syscalls and inline machine
code all work. Deliberately absent: generics, closures, methods, namespaces,
threads, exceptions, garbage collection, bounds checking. See the end of
SPEC.md.
