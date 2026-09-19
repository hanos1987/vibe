# VIBE

A systems language with no natural-language keywords, compiled straight to
x86-64 machine code. `vibec` writes the ELF bytes itself — there is no
assembler, no linker, no C library and no runtime anywhere in the pipeline.
For release builds, `vibec --backend=c` sends the same program through gcc
or clang at `-O3` and runs as fast as C.

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
| Any Linux, macOS | `curl -fsSL https://raw.githubusercontent.com/hanos1987/vibe/master/install.sh \| sh` |
| Debian / Ubuntu | `sudo apt install vibe` after adding the repository below, or download `vibe_0.4.0_all.deb` from the [release](https://github.com/hanos1987/vibe/releases/latest) and `sudo apt install ./vibe_0.4.0_all.deb` |
| Any, with pip | `pipx install https://github.com/hanos1987/vibe/releases/download/v0.4.0/vibe_lang-0.4.0-py3-none-any.whl` |
| Windows | `irm https://raw.githubusercontent.com/hanos1987/vibe/master/install.ps1 \| iex` |
| From source | `git clone https://github.com/hanos1987/vibe && cd vibe && ./install.sh` |

`--backend=c` additionally needs gcc or clang on the PATH.

APT repository (signed):

```sh
curl -fsSL https://benjiapps.com/vibe/apt/vibe.gpg \
  | sudo tee /usr/share/keyrings/vibe.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/vibe.gpg] https://benjiapps.com/vibe/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/vibe.list
sudo apt update && sudo apt install vibe
```

Build every release artifact yourself with `packaging/release.sh`, and the
APT repository with `packaging/mkrepo.sh --sign <key>`.

## Why it looks like this

Three rules, each removing an ambiguity that generated code gets wrong:

1. **No operator precedence.** `1 + 2 * 3` is rejected; write
   `1 + (2 * 3)`. An expression means what its shape says.
2. **No implicit conversions.** `s64 + s32` is rejected. Nothing changes
   representation silently.
3. **One statement per line.** No semicolons, no line joining.

Plus: matches must be exhaustive, mutation requires `$~`, every path must
return, literals must fit their type, and every construct is a single sigil,
so nothing depends on knowing English.

## What is in the language

| | |
|---|---|
| Types | sized ints, floats, bool, pointers, arrays, structs, tagged sums, function pointers |
| Generics | `%Vec<T>`, `@ push<T> (...)`, monomorphised, with inference |
| Methods, errors | `v.push(3)` calls `push(&v, 3)`; `%Res<T,E>` / `%Opt<T>` with `!` propagation |
| Formatting | `\print("x={} y={.2}\n", x, y)`, `\fmt` |
| Control | `?` `:` if/else, `*` loops, `* i 0 n` counted loops, `??` exhaustive match, `~` defer |
| Modules | `<<"file"` flat include, `<<"file" ns` namespaced include |
| SIMD | `f32x4 f64x2 s32x4` (native SSE), `f32x8 f64x4 s32x8` (AVX2 via C backend), lane-wise operators, `\vsum \vget \vsqrt \vmin \vmax` |
| Machine | `\N` syscalls, `\sqrt \popcnt \cas \xadd ...` intrinsics, `\\[..]` raw bytes |
| Threads | `spawn` / `join` kernel threads, atomics, spin locks, thread-safe heap |
| C interop | `@< "lib" name (T, ...) R` calls any C library |
| Library | strings, files, processes, sockets, time, maths, heap, `%Buf`, `%Vec<T>`, `%Map<V>`, `%IMap<V>` |
| Tooling | `--check` bounds traps, `--json` diagnostics, ELF symbols for gdb/perf, all errors in one run, two differential fuzzers, `tools/restyle.py` |

## What you can build with it

Every category below is covered by a program in this repository that runs.

| Category | Proof | What it needs |
|---|---|---|
| Games, terminal UI | `examples/snake.vibe` | raw mode, non-blocking input, frame timing |
| Command line tools | `examples/wc.vibe` | argv, file i/o, heap |
| Network services | `examples/httpd.vibe` | sockets, bind/listen/accept |
| Parallel compute | `examples/par.vibe`, `tests/t22_threads.vibe` | fork and pipes; threads and atomics |
| Data structures | `tests/t23_generics.vibe`, `vibelang/stdlib/heap.vibe` | generics, allocator, hash map |
| Using C libraries | `tests/t20_ffi.vibe` | `@<` declarations, libc and libm |
| Numerics | `vibelang/stdlib/math.vibe` | f64, sqrt/exp/log/trig |
| Systems, embedded | the compiler's own output | syscalls, inline machine code |

`examples/wc.vibe` produces byte-identical output to GNU `wc`.
`examples/httpd.vibe` serves real HTTP to `curl`.

Anything with a C API — GUI toolkits, databases, GPU runtimes, compression,
TLS — is reachable through `@<`.

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
  cback.py           IR to freestanding C, for --backend=c
  names.py           namespaced includes
  elf.py             static ELF64 writer
  stdlib/            std, sys, math, heap, thread — all written in VIBE
examples/            snake, wc, httpd, par
tests/               behavioural and diagnostic tests
bench/               benchmarks against gcc
packaging/           .deb, APT repo, release artifacts
tools/               IR and disassembly dumps
```

## Running the tests

```
python3 tests/run.py              # native, optimised
python3 tests/run.py -O0          # every value in memory, no allocation
python3 tests/run.py --backend=c  # through the C compiler
python3 tests/fuzz.py 0 1000      # random programs, -O against -O0
python3 tests/fuzz4.py 0 500      # richer programs, all three paths
```

All three paths must agree; `-O0` exists as an independent oracle for the
optimiser, and the fuzzer compares the two on random programs.

## Benchmarks

Identical programs, least user CPU time of seven runs, outputs verified
equal (`python3 bench/run.py`).

| bench | VIBE native | VIBE `--backend=c` | gcc -O0 | gcc -O2 | gcc -O3 |
|---|---|---|---|---|---|
| fib(35) | 0.033s | 0.018s | 0.062s | 0.029s | 0.017s |
| sieve 10M | 0.022s | 0.025s | 0.071s | 0.025s | 0.026s |
| matmul 400 | 0.074s | 0.051s | 0.160s | 0.037s | 0.035s |
| mandel 900² | 0.052s | 0.047s | 0.146s | 0.042s | 0.040s |

Through the C backend VIBE runs level with gcc `-O3` on the same algorithm,
because it *is* gcc's optimiser working on VIBE's program. The native
backend — a dozen optimisation passes in Python, no toolchain at all — runs
2-3x faster than `gcc -O0` and between parity and about 1.7x of `gcc -O2`
(sieve and byte-scanning loops at parity; recursion and float loops behind;
nothing is vectorised).

Token cost matters when a model writes the code. On the same four programs,
idiomatic VIBE costs 0.99x the tokens of the C (o200k tokenizer;
`python3 tools/tokens.py`), with no operator precedence to get wrong.

A native VIBE hello world is 912 bytes (319 stripped) where the equivalent
static C binary is 785 KB, because there is no libc to carry.

```
python3 bench/run.py
```

## Status

v0.3. Everything in the table above works on all three build paths and is
covered by the test suite. Deliberately absent: closures, methods,
exceptions, garbage collection. The native backend targets x86-64 Linux
only. See the end of SPEC.md.
