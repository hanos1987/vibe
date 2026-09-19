# VIBE — Language Specification v0.3

VIBE is a systems language with **no natural-language keywords**. Every
construct is a sigil. It compiles straight to x86-64 machine code: `vibec`
writes the ELF bytes itself, with no assembler, no linker, no C library and
no runtime. A second backend, `--backend=c`, hands the same program to
gcc or clang at `-O3` for release builds that run as fast as C.

It is designed to be written by a model. The three rules below exist because
they remove the ambiguities that generated code gets wrong most often.

**Rule 1 — There is no operator precedence.**
`1 + 2 * 3` is a compile error. Write `1 + (2 * 3)`. Two *different*
operators never share a level, so an expression means exactly what its shape
says. A level with one operator needs no parentheses of its own: `^ a + b`,
`? i < n {`, `f(i * 2, 1)` are all fine.

**Rule 2 — There are no implicit conversions.**
`s64 + s32` is a compile error. Widths are converted only when you write
`s64(x)`. Nothing changes representation behind your back.

**Rule 3 — One statement per line.**
A newline ends a statement. There are no semicolons and no line joining.

---

## 1. Sigil reference

The whole language, in one table.

| Sigil | Meaning | Example |
|---|---|---|
| `;` | comment to end of line | `; a note` |
| `<<"f"` | include a file once | `<<"std.vibe"` |
| `@` | function | `@ add (a s64, b s64) s64 { ^ (a + b) }` |
| `@!` | entry point; returns the exit status | `@! () s64 { ^ 0 }` |
| `%` | struct declaration | `%Pt { x s64, y s64 }` |
| `%\|` | sum (tagged union) declaration | `%\| R { \|Ok(s64), \|Err }` |
| `$` | immutable binding | `$ x s64 = 1` |
| `$~` | mutable binding | `$~ x s64 = 1` |
| `$$` | compile-time constant | `$$ N s64 = 64` |
| `=` | assignment | `x = 2` |
| `+=` `-=` `*=` `/=` `%=` `&=` `\|=` `^=` `<<=` `>>=` | compound assignment | `t += 1` |
| `^` | return (bare `^` returns from a `v` function) | `^ x` |
| `?` `:` | if / else | `? c { } : { }` |
| `??` `\|` | match / arm | `?? r { \|Ok(v) { } \|Err { } }` |
| `_` | wildcard arm (must be last) | `\|_ { }` |
| `*` | loop while | `* i < n { }` |
| `* i a b` | counted loop, `i` from `a` up to but not including `b` | `* i 0 n { }` |
| `~` | defer a statement to scope exit | `~ fc(fd)` |
| `*<` | break | `*<` |
| `*>` | continue | `*>` |
| `\N` | syscall number N | `\1(1, p, n)` |
| `\name` | compiler intrinsic | `\sqrt(x)`, `\cas(&v, 0, 1)` |
| `\\[..]` | inline machine code bytes | `\\[0x90]` |
| `@<` | declare a C function | `@< "m" pow (f64, f64) f64` |
| `<T>` | type parameters and arguments | `%Vec<T> { }`, `@ push<T> (...)`, `%Vec<s64>` |
| `<<"f" ns` | include under a namespace | `<<"geom.vibe" g` then `g.area(p)` |
| `x.f(a)` | method call: `f(x, a)`, or `f(&x, a)` | `v.push(3)` |
| `e!` | unwrap a `%Res`/`%Opt`, or return its failure | `$ n = parse(s)!` |
| `\fmt` `\print` `\eprint` | formatting | `\print("x={} y={.2}\n", x, y)` |
| `&` | address of | `&x` |
| `'` | dereference (postfix) | `p'` |
| `.` | field | `p.x` |
| `[ ]` | index | `a[i]` |
| `#` | size of a type, in bytes | `#s64` |
| `T( )` | cast | `s64(c)`, `*u8(p)` |
| `%N{ }` | struct literal | `%Pt{ x: 1, y: 2 }` |
| `%N\|V( )` | sum value | `%R\|Ok(5)` |
| `[a, b]` | array literal | `[1, 2, 3]` |
| `` ` `` | byte literal | `` `A ``, `` `\n `` |
| `@(T)R` | function-pointer **type** | `@(s64, s64) s64` |
| `@name` | address of a function | `$ f @(s64) s64 = @double` |

Identifiers are yours: letters, digits and `_`, plus any non-ASCII
character, so names may be written in any script.

---

## 2. Types

| Notation | Meaning |
|---|---|
| `s8 s16 s32 s64` | signed integers |
| `u8 u16 u32 u64` | unsigned integers |
| `f32 f64` | IEEE floats |
| `b` | boolean, one byte, `0` or `1` |
| `v` | void; only a return type |
| `*T` | pointer to T |
| `[N]T` | array of N T, N a literal |
| `f32x4 f64x2 s32x4` | SIMD vectors: 4 x f32, 2 x f64, 4 x s32 in one register |
| `f32x8 f64x4 s32x8` | 256-bit vectors (AVX2; built through the C backend) |
| `%Name` | a declared struct or sum type |
| `@(T, ...) R` | pointer to a function taking T... returning R |

One type is built in:

```
%Str { p *u8, n s64 }
```

A string literal `"hi"` has type `%Str`. `.p` points at the bytes (which are
NUL-terminated, though `.n` excludes the NUL), and `.n` is the byte length.

Structs use natural alignment. A sum type is an `s64` tag at offset 0
followed by the payload. Types are laid out in dependency order, so a struct
may embed a struct declared later in the file. Types may only contain each
other **through a pointer**; embedding by value in a cycle is an error.

---

## 3. Declarations

All declarations are top level. Order does not matter — functions and types
may be used before they appear.

```
<<"std.vibe"                        ; include; each file is loaded once

%Pt { x s64, y s64 }                ; struct

%| Res {                            ; sum type
  |Ok(s64)
  |Err(%Str)
  |None
}

$$ LIMIT s64 = 4096                 ; compile-time constant, no storage
$  origin s64 = 0                   ; immutable global
$~ hits   s64 = 0                   ; mutable global
$~ table  [16]s64                   ; no value given: zero-initialised

@ add (a s64, b s64) s64 {          ; function
  ^ (a + b)
}

@! () s64 {                         ; entry point: exactly one per program
  ^ 0                               ; the returned s64 is the exit status
}
```

A global initialiser must be a compile-time constant: a scalar, or an array
or struct literal built from constants, string literals and `@function`
addresses. That is enough for lookup tables, message tables and dispatch
tables:

```
$ days [12]u8 = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
$ names [2]%Str = ["off", "on"]
$ cmds [2]%Cmd = [%Cmd{ name: "dbl", run: @dbl }, %Cmd{ name: "neg", run: @neg }]
```

A short array literal leaves the rest zeroed. A global set to a plain
integer or float literal needs no type: `$~ total = 0` is an `s64`,
`$ rate = 0.5` an `f64`. `$$` constants are inlined at every use, have no
address, and may be built from other `$$` constants, `#T`, and (for floats)
literals, casts and arithmetic: `$$ TAU f64 = 2.0 * 3.14159`.

Functions take any number of parameters. A function with a return type
must return on every path; falling off the end is a compile error.

---

## 4. Statements

One per line.

```
$ x s64 = 5              ; immutable binding
$~ y s64 = 5             ; mutable binding
$~ buf [64]u8            ; type only: zero-initialised
$ z = (x + 1)            ; type inferred from the value

y = 7                    ; assignment (only to $~ bindings and memory)
p' = 7                   ; through a pointer
a[i] = 7                 ; into an array
s.field = 7              ; into a struct

^ e                      ; return a value
^                        ; return from a `v` function

? c { }                  ; if
? c { } : { }            ; if / else
? c { } : ? d { } : { }  ; else-if chains

* c { }                  ; loop while c
* i 0 n { }              ; counted: i = 0, 1, ... n-1   (n is read once)
*<                       ; break
*>                       ; continue (in a counted loop: on to the next i)

x += 1                   ; compound assignment: + - * / % & | ^ << >>
~ fc(fd)                 ; defer: runs when the enclosing block exits

?? subject { |A(x) { } |B { } }     ; match

f(1, 2)                  ; call as a statement
\1(1, s.p, s.n)          ; syscall as a statement
\\[0x0f, 0x05]           ; raw machine code bytes
```

A binding is visible from its line to the end of the enclosing block. A
name may not be bound twice in one block.

The counted loop `* i a b { }` binds `i` for the body only. `a` is a bare
name or number (a number may be negative: `* z -3 4 { }`); `b` is a single operand, so parenthesise an
expression: `* i 2 (n + 1) { }`. Both must have the same integer
type (a literal takes the type of the other), and `i` has that type.

The target of a compound assignment is evaluated twice, so it may not
contain a call: `a[f()] += 1` is rejected.

`~ stmt` defers a call or an assignment. Deferred statements run in reverse
order when their block exits by any route: falling off the end, `^`, `*<` or
`*>`. A returned value is computed *before* the deferred statements run.

```
@ load (path *u8) s64 {
  $ fd s64 = fo(path, O_RDONLY, 0)
  ? fd < 0 {
    ^ -1
  }
  ~ fc(fd)                 ; closed on every return below
  ...
}
```

The `:` of an else may follow the closing brace on the same line or start
the next line.

Conditions must have type `b`. There is no truthiness: write `(x != 0)`.

---

## 5. Expressions

### Operators

```
arithmetic   +  -  *  /  %
bitwise      &  |  ^  <<  >>
compare      ==  !=  <  <=  >  >=
logical      &&  ||          (short-circuit, operands are b)
unary        -e   ~e (bitwise not)   !e (logical not, b)
```

**No precedence.** Operands of a binary operator may not themselves be
unparenthesised binary expressions:

```
1 + (2 * 3)          ; fine
1 + 2 + 3            ; fine: a chain of one associative operator
1 + 2 * 3            ; error: mixed operators need parentheses
a < b < c            ; error: comparisons never chain
10 - 3 - 2           ; error: - / % << >> do not chain either
```

Only `+ * & | ^ && ||` chain, because only for them does grouping not
matter.

### Conversions

None are implicit. Both sides of a binary operator must already have the
same type. Use a cast:

```
$ a s64 = 1
$ b s32 = 2
$ c s64 = (a + s64(b))
```

Two exceptions, both safe and unambiguous:

* A **literal** takes the type it is used at: `$ x u8 = 200`, `5 == x`,
  `$ h f64 = 5`, `h * 2`. It must fit: `$ x u8 = 300` is an error.
* An **array decays to a pointer** where a pointer is expected:
  passing `[16]u8` to a `*u8` parameter is fine.

### Semantics worth stating

* `/` and `%` truncate toward zero: `(-7 / 2)` is `-3`, `(-7 % 2)` is `-1`.
* `>>` is arithmetic on signed types and logical on unsigned.
* Sized integers wrap at their own width: `u8` 250 + 10 is 4.
* Pointer arithmetic scales by the pointee size. `(p + 1)` advances one
  element. `(p - q)` on two pointers yields the element count as `s64`.
* `&&` and `||` do not evaluate their right operand unless they must.
* Comparing two pointers is allowed; mixing pointer and integer is not.
* `==` and `!=` on two `%Str` compare the bytes (it calls `seq`, so
  `std.vibe` must be included). On any other struct they are an error.
* Float comparisons follow IEEE 754: every comparison with a NaN is false
  except `!=`. `-x` flips the sign bit, so `-(0.0)` is `-0.0`.
* `b(x)` is `x != 0`.
* A float converted to an integer truncates toward zero; a value that does
  not fit (or a NaN) gives the most negative `s64`.
* Assigning one aggregate to another reads the whole value before writing
  any of it, so overlapping source and destination are safe.

### Postfix and prefix forms

```
p'          dereference               (postfix apostrophe)
&x          address of
s.f         field of a struct         (auto-dereferences *%S)
a[i]        index an array or pointer
#s64        size in bytes of a type
s64(x)      cast to a primitive
*u8(x)      cast to a pointer
```

### Function pointers

`@(T, ...) R` is the type of a pointer to a function. `@name` is the address
of a declared function. Calling one uses the same syntax, and the same ABI,
as a direct call.

```
@ add (a s64, b s64) s64 { ^ (a + b) }
@ mul (a s64, b s64) s64 { ^ (a * b) }

; a function taken as a parameter
@ fold (p *s64, n s64, seed s64, op @(s64, s64) s64) s64 {
  $~ acc s64 = seed
  $~ i s64 = 0
  * (i < n) {
    acc = op(acc, p[i])
    i = (i + 1)
  }
  ^ acc
}

; a function returned from a function
@ pick (k s64) @(s64, s64) s64 {
  ? (k == 0) {
    ^ @add
  }
  ^ @mul
}

@! () s64 {
  $ f @(s64, s64) s64 = @add
  ^ f(3, 4)                      ; 7
  ; pick(1)(3, 4) also works: the result of a call is callable
}
```

Function pointers are scalars, so they live in struct fields and arrays,
which is all a dispatch table needs. They compare by identity with `==` and
`!=`. There is no capture: VIBE has function pointers, not closures.

---

## 6. Pattern matching

```
%| Shape {
  |Dot
  |Line(s64, s64)
  |Box(%Pt)
}

@ area (s %Shape) s64 {
  ?? s {
    |Dot        { ^ 0 }
    |Line(a, b) { ^ (b - a) }
    |Box(p)     { ^ (p.x * p.y) }
  }
  ^ -1
}
```

A match **must be exhaustive**. Cover every variant, or end with `|_`, or
the compiler rejects the program and names the missing variants. Binder
count must equal the variant's payload count. Binders are immutable copies,
scoped to their arm.

---

## 7. Talking to the machine

There is no runtime and no libc. The kernel is reached directly.

```
\N(a1, ..., a6)
```

is Linux syscall number `N`, up to six scalar arguments, result as `s64`.
Common ones: `\0` read, `\1` write, `\9` mmap, `\11` munmap, `\60` exit.

```
@! () s64 {
  $ s %Str = "hello\n"
  \1(1, s.p, s.n)
  ^ 0
}
```

Raw bytes can be emitted where nothing else will do:

```
\\[0x0f, 0x31]        ; rdtsc
```

The bytes are inserted verbatim into the instruction stream. Nothing is
checked; the register allocator does not know what they touch.

---

### Methods

`x.f(a)` calls `f(x, a)` whenever `x` has no field named `f` and a function
`f` exists. When `f`'s first parameter is a pointer, `x` is passed by
address, so mutating "methods" work on plain values:

```
@ push<T> (w *%Vec<T>, x T) v { ... }
@ len<T> (w %Vec<T>) s64 { ^ w.n }

v.push(3)          ; push(&v, 3)
v.len()            ; len(v)
```

Any function is a method of its first argument. There is no receiver
type, no dispatch table and no hidden `this`.

### Results and `!`

`std.vibe` defines two generic sum types:

```
%| Res<T, E> { |Ok(T) |Err(E) }
%| Opt<T>    { |Some(T) |None }
```

A postfix `!` on a `%Res<T, E>` value yields the `T`, or returns the `Err`
from the enclosing function, which must itself return a `%Res<_, E>` with
the same `E`. On a `%Opt<T>` it yields the `T` or returns `%Opt|None`.
Deferred statements run on that early return like on any other.

```
@ calc (a s64, b s64) %Res<s64, %Str> {
  $ q = div(a, b)!
  $ h = half(q)!
  ^ %Res|Ok(h + 1)
}
```

### Formatting

```
\print("x={} y={.2} hex={x} c={c} {{literal}}\n", x, y, n, ch)
\eprint("bad input: {}\n", line)
$ s = \fmt("{}-{}", a, b)        ; a heap %Str; del(s.p) when done
```

`{}` prints by type: integers in decimal, floats with six decimals (values
of 10^18 and above in exponent form, `inf`/`nan` as such), `%Str` and `*u8`
as text (a null `*u8` as `(null)`), `b` as 0/1, other pointers in hex. `{.N}` sets a float's
decimals, `{x}` prints an integer in hex, `{c}` a `u8` as a character.
Formatting needs `<<"heap.vibe"`.

### SIMD vectors

A vector holds several numbers in one CPU register and operates on all of
them with one instruction.

```
@ dot (a *f32, b *f32, n s64) f32 {
  $~ acc f32x4                        ; four lanes, all zero
  $~ i = 0
  * (i + 4) <= n {
    acc += *f32x4(a + i)' * *f32x4(b + i)'
    i += 4
  }
  $~ s = \vsum(acc)
  * i < n {                           ; the tail, one at a time
    s += a[i] * b[i]
    i += 1
  }
  ^ s
}
```

* `f32x4(x)` broadcasts a scalar to every lane; a literal next to a vector
  broadcasts by itself (`v * 0.5`).
* `+ - * /` work lane by lane on float vectors; `+ - * & | ^` on `s32`
  vectors. Both operands must be the same vector type.
* Memory is reached through a vector pointer: `*f32x4(p)'` loads four
  `f32` starting at `p`, and assigning to it stores them. No alignment is
  required.
* `\vsum(v)` adds the lanes (pairwise: `(l0+l1)+(l2+l3)`), `\vget(v, 2)`
  reads one lane (the lane is a literal), `\vsqrt(v)`, `\vmin(a, b)` and
  `\vmax(a, b)` work lane by lane.
* Vectors are values: they can be locals, parameters, results, struct
  fields and array elements. They cannot be compared, formatted or passed
  through a function pointer.

The 128-bit types compile natively to SSE; `s32` multiply, min and max need
SSE4.1. The 256-bit types need AVX2 and are built through the C backend
automatically.

### Intrinsics

`\name(...)` is an operation the compiler emits directly, usually as one
instruction.

| Intrinsic | Type | Meaning |
|---|---|---|
| `\sqrt(x)` | `f64 -> f64`, `f32 -> f32` | hardware square root |
| `\bits(x)` `\fbits(u)` | `f64 -> u64`, `u64 -> f64` | reinterpret the bits |
| `\popcnt(x)` `\clz(x)` `\ctz(x)` | 64-bit int | bit counts (`clz`/`ctz` of 0 is 64) |
| `\bswap(x)` | 64-bit int | reverse the bytes |
| `\rdtsc()` | `u64` | CPU timestamp counter |
| `\cas(p, old, new)` | `b` | atomic compare-and-swap of the 64-bit cell at `p` |
| `\xadd(p, d)` | old value | atomic fetch-and-add |
| `\load(p)` `\store(p, x)` | 64-bit cell | access memory another thread may change |
| `\pause()` | `v` | spin-wait hint |
| `\clone(f, arg, top, tid)` | `s64` | start a kernel thread; use `spawn` from `thread.vibe` |

`\popcnt`, `\clz` and `\ctz` need a CPU from about 2013 on (Haswell / Zen).

### Calling C

```
@< "c" printf (fmt *u8, ...) s32
@< "m" pow (f64, f64) f64

@! () s64 {
  printf("%lld %.2f\n".p, 42, pow(2.0, 0.5))
  ^ 0
}
```

`@< "lib" name (types) ret` declares a function from a C library; `"c"` is
libc, anything else is linked with `-l<lib>`. Parameter names are optional.
When the C name collides with a VIBE name, give it another:
`@< "c" cabs = abs (s32) s32` calls C's `abs` as `cabs`.
Arguments and results are scalars and pointers. After `...`, integers and
pointers are passed as 64-bit and floats as `f64`. Pass `s.p`, never a
`%Str`; string literals are NUL-terminated for exactly this purpose. A
program that declares C functions is built through the C backend and linked
against the C runtime automatically. The address of a C function cannot be
taken (`@strlen`); wrap it in a VIBE function.

---

## 8. Generics

Types and functions may take type parameters. Each distinct set of type
arguments gets its own compiled copy, so generic code costs nothing at run
time.

```
%Vec<T> { p *T, n s64, cap s64 }

%| Opt<T> {
  |Some(T)
  |None
}

@ push<T> (w *%Vec<T>, x T) v {
  ...
  w.p[w.n] = x
  w.n += 1
}

@ last<T> (w *%Vec<T>) %Opt<T> {
  ? w.n == 0 {
    ^ %Opt|None                   ; type arguments come from the return type
  }
  ^ %Opt|Some(w.p[w.n - 1])
}

@! () s64 {
  $~ a %Vec<s64> = vnew()         ; T from the expected type
  push(&a, 10)                    ; T from the argument
  $~ f = vnew<f64>()              ; or stated outright
  ^ 0
}
```

Type arguments are inferred from the non-literal arguments and from the type
the context expects; a literal left to decide a parameter makes it `s64` or
`f64`. If that is not enough, write them: `f<s64>(...)`.
Inside a generic, `T(x)` is a cast to `T` and `#T` is its size. A generic
struct or sum literal may omit its arguments where the expected type
supplies them (`%Vec{ ... }`, `%Opt|None`).

---

## 9. Namespaces

```
<<"geom.vibe" g

$ p %g.Pt = %g.Pt{ x: 1, y: 2 }
pnl(g.area(p))
$ f @(%g.Pt) s64 = @g.norm
```

`<<"file" name` includes a file, and everything it includes, under a
namespace: its functions, types, globals and constants are reachable only as
`name.thing`. Inside the file nothing changes. Use it for your own modules,
and whenever a library's names collide with yours. A plain `<<"file"` shares
one flat namespace, which is how the standard library is normally used.

A program may declare a name the library already uses. The program's
definition is the one the program sees; the library keeps calling its own
version, so redefining `max` or `beq` changes nothing inside `std.vibe`.

---

## 10. Standard library

The library is written in VIBE. `<<"std.vibe"` pulls in the core and the
system layer; `<<"math.vibe"` is separate because floating point maths is
not wanted by every program. Functions you do not call are not emitted, so
including the library costs nothing.

One name comes from the compiler rather than the library: `__sp` is the
stack pointer the kernel handed the process, and `argc`/`argv`/`envp` are
read from it. Everything else below is ordinary VIBE.

### Core (`std.vibe`)

| Name | Signature | Purpose |
|---|---|---|
| `ex` | `(c s64) v` | exit |
| `wr` | `(fd s64, p *u8, n s64) s64` | write |
| `rd` | `(fd s64, p *u8, n s64) s64` | read |
| `ps` | `(s %Str) v` | print a string |
| `pe` | `(s %Str) v` | print to stderr |
| `pc` | `(c u8) v` | print one byte |
| `nl` | `() v` | newline |
| `pn` | `(x s64) v` | print a signed decimal |
| `pnl` | `(x s64) v` | print a decimal and a newline |
| `px` | `(x u64) v` | print lowercase hex |
| `mm` | `(n s64) *u8` | map n bytes; 0 on failure |
| `mu` | `(p *u8, n s64) v` | unmap |
| `cp` | `(d *u8, s *u8, n s64) v` | copy bytes |
| `set` | `(d *u8, c u8, n s64) v` | fill bytes |
| `ln` | `(p *u8) s64` | length to NUL |
| `beq` | `(a *u8, b *u8, n s64) b` | compare bytes |
| `seq` | `(a %Str, b %Str) b` | compare strings |
| `abs` `min` `max` | `(s64 ...) s64` | integer helpers |
| `lock` `unlock` | `(l *s64) v` | spin lock; the s64 starts at 0 |
| `ssub` `sidx` `sfind` `sstarts` `sends` `strim` | string views | slice, search, trim; nothing is copied |
| `stok` | `(rest *%Str, sep u8, done *b) %Str` | next field up to `sep` |
| `sint` `sfloat` | `(s %Str)` | parse a decimal integer / float |
| `uchars` `ulen` | UTF-8 | character count, bytes in a character |
| `%Res<T,E>` `%Opt<T>` | | see section 7 |
| `print` `println` `printi` `printiln` `eprint` `exit` `copy` `fill` `cstrlen` | | long names for `ps`, `ps`+`nl`, `pn`, `pnl`, `pe`, `ex`, `cp`, `set`, `ln` |

### System (`sys.vibe`, included by `std.vibe`)

| Name | Signature | Purpose |
|---|---|---|
| `argc` | `() s64` | argument count |
| `arg` | `(i s64) %Str` | argument i |
| `argp` | `(i s64) *u8` | argument i as a C string |
| `env` | `(name %Str) %Str` | environment variable, empty if unset |
| `alloc` | `(n s64) *u8` | arena allocation; no free |
| `nat` | `(s %Str) s64` | decimal to integer |
| `pf` `pfl` | `(x f64, dp s64) v` | print a float, rounded to dp places |
| `fo` `fc` `fsz` | file descriptor calls | open, close, size |
| `fall` | `(path *u8) %Str` | read a whole file |
| `now_ns` | `() s64` | monotonic nanoseconds |
| `nap` | `(ms s64) v` | sleep |
| `fork` `pid` `waitpid` | process control | concurrency is by process |
| `exec` `pip` `dup2` | process plumbing | run programs, pipes, redirection |
| `srv` | `(port s64) s64` | bind and listen on a TCP port |
| `acc` | `(fd s64) s64` | accept a connection |

### Heap and containers (`heap.vibe`, include it yourself)

| Name | Signature | Purpose |
|---|---|---|
| `new` | `(n s64) *u8` | allocate; thread-safe |
| `del` | `(p *u8) v` | free; `del(0)` is a no-op |
| `renew` | `(p *u8, n s64) *u8` | resize, keeping contents |
| `%Buf` `bnew` `bpc` `bpb` `bps` `bpn` `bpu` `bpf` `bpx` `bstr` `bfree` | | growable byte buffer / string builder |
| `%Vec<T>` `vnew` `vpush` `vpop` `vlast` `vdel` `vreserve` `vfree` | | growable array (`w.p[i]` to index, `w.n` elements) |
| `%Map<V>` `mnew` `mset` `mget` `mref` `mhas` `mdel` `mfree` | | hash map from `%Str` to V (keys are not copied) |
| `%IMap<V>` `inew` `iset` `iget` `ihas` `idel` `ifree` | | hash map from `s64` to V |

All take the container by pointer, so `v.vpush(x)` and `m.mget("k", 0)`
read naturally.

### Threads (`thread.vibe`, include it yourself)

| Name | Signature | Purpose |
|---|---|---|
| `spawn` | `(f @(s64) v, arg s64) *%Thread` | run `f(arg)` on a new kernel thread with its own 1 MB stack |
| `join` | `(t *%Thread) v` | wait for it and release its stack |
| `%Lock` `acquire` `release` | `(l *%Lock) v` | a lock whose waiters sleep (futex); for anything but tiny sections |

Each thread stack has an inaccessible guard page below it, so an overflow
traps instead of corrupting memory.

Threads share all memory. Protect shared data with `lock`/`unlock`, or with
`\cas` / `\xadd`. Memory that another thread may change outside a lock must
be read and written with `\load` / `\store`; an optimiser may cache or reorder
plain accesses. A program that declares C functions should use the C
library's threads instead.

### Maths (`math.vibe`, include it yourself)

| Name | Purpose |
|---|---|
| `M_PI` `M_TAU` `M_E` `M_LN2` | constants |
| `fabs` `floor` `ceil` `fmod` `fmin` `fmax` | rounding and comparison |
| `sqrt` `hypot` `pow` | roots and powers |
| `exp` `lg` `log10` | exponential and logarithms (`lg` is natural log) |
| `sin` `cos` `tan` | trigonometry |

`ln` in the core library is byte-string length; the natural logarithm is
`lg`. They are different functions with deliberately different names.

---

## 11. Using the compiler

```
vibec prog.vibe -o prog     compile to a static executable
vibec prog.vibe --run       compile and run
vibec prog.vibe --ir        print the mid-level IR
vibec prog.vibe -O0 ...     no optimisation, no register allocation
vibec prog.vibe --backend=c build through gcc or clang -O3
vibec prog.vibe --emit-c    print the generated C
vibec prog.vibe --check     trap, with file:line, on a bad array index or
                            a division by zero
vibec prog.vibe --json      report errors as JSON on stdout
vibec prog.vibe -s          strip the symbol table
python3 tools/restyle.py f.vibe   rewrite a file in the economical style
```

Native binaries carry an ELF symbol table, so `gdb`, `perf` and `objdump`
name VIBE functions; `-s` drops it (a stripped hello world is about 300
bytes). Small functions are inlined by the optimiser, so at `-O` their
symbols may be absent; build with `-O0` to break on any function.

**Two backends, one language.** The native backend needs nothing but
Python and is the default: builds are instant and the binaries are tiny.
`--backend=c` prints the same program as freestanding C and compiles it with
`-O3`; the result is still a static executable with no libc, and it runs as
fast as the equivalent C. Set `VIBE_CC` to choose the C compiler and
`VIBE_CFLAGS` to add flags (for example `-march=native`). Develop with the
native backend, ship with the C backend.

Errors are reported one per function, all in one run, as
`file:line:col: message`.

The output is a static ELF64 executable that runs on Linux x86-64 with no
shared libraries. `-O0` compiles through a separate path where every value
lives in memory; it exists so any program can be run two ways and compared.

---

## 12. Grammar

```
unit     := decl*
decl     := include | fn | extern | struct | sum | global
include  := '<<' STRING IDENT? NL
fn       := ('@' IDENT tparams? | '@!') '(' params? ')' type block NL
extern   := '@<' STRING IDENT '(' (IDENT? type (',' IDENT? type)*)? (',' '...')? ')' type NL
params   := IDENT type (',' IDENT type)*
tparams  := '<' IDENT (',' IDENT)* '>'
targs    := '<' type (',' type)* '>'
struct   := '%' IDENT tparams? '{' (IDENT type ','?)* '}' NL
sum      := '%|' IDENT tparams? '{' ('|' IDENT ('(' type (',' type)* ')')? ','?)* '}' NL
global   := ('$' | '$~' | '$$') IDENT type ('=' expr)? NL

name     := IDENT ('.' IDENT)?                    -- ns.name
type     := 's8'|'s16'|'s32'|'s64'|'u8'|'u16'|'u32'|'u64'
          | 'f32'|'f64'|'b'|'v' | IDENT           -- IDENT: a type parameter
          | '*' type | '[' (INT|IDENT) ']' type | '%' name targs?
          | '@' '(' (type (',' type)*)? ')' type

block    := '{' NL stmt* '}'
stmt     := ('$'|'$~') IDENT (type)? ('=' expr)? NL
          | expr ('=' | '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|='
                  | '^=' | '<<=' | '>>=') expr NL
          | '^' expr? NL
          | '?' expr block (NL* ':' (block | stmt))? NL
          | '*' expr block NL
          | '*' IDENT (INT|IDENT) unary block NL  -- counted loop
          | '*<' NL | '*>' NL
          | '~' stmt                              -- defer
          | '??' expr '{' NL arm* '}' NL
          | '\\\\' '[' INT (',' INT)* ']' NL
          | expr NL
arm      := '|' (IDENT ('(' IDENT (',' IDENT)* ')')? | '_') block

expr     := unary (binop unary)*        -- one distinct operator per level
unary    := ('-'|'!'|'~') unary | '&' unary | '#' type | postfix
postfix  := primary ("'" | '.' IDENT | '[' expr ']' | targs? '(' args? ')')*
primary  := INT | FLOAT | STRING | BYTE | IDENT
          | '(' expr ')'
          | '[' expr (',' expr)* ']'
          | '\\' INT '(' args? ')'                 -- syscall
          | '\\' IDENT '(' args? ')'               -- intrinsic
          | '%' name targs? '{' (IDENT ':' expr ','?)* '}'
          | '%' name targs? '|' IDENT ('(' args? ')')?
          | '@' name
          | prim_type '(' expr ')' | '*' type '(' expr ')'
```

`*<` and `*>` are tokens only at the start of a statement, so `(a*<b)` is a
multiply and a compare. A statement that begins `*T(` with `T` a type is a
store through a cast pointer (`*s64(p)' = 5`), not a loop.

---

## 13. Calling convention and layout

* Scalar arguments go in `rdi, rsi, rdx, rcx, r8, r9`; floats in `xmm0`
  upward; the result is in `rax` or `xmm0`.
* Aggregates are passed by value: the caller makes a copy and passes its
  address. An aggregate return is written through a hidden first argument.
* The binary has two segments: read+execute for code and constants,
  read+write for globals. There is no interpreter and no dynamic section.

---

## 14. What v0.2 does not have

Stated plainly so nothing is inferred that is not there: no closures
(function pointers do not capture; pass a context pointer), no methods,
interfaces or overloading, no exceptions (return a sum type and match on
it), no garbage collector, no string formatting beyond the `%Buf` appenders,
and no targets other than x86-64 Linux in the native backend. `u64`-to-float
conversion is exact only below 2^63. Bounds are checked only under
`--check`.

Memory safety is the programmer's job, exactly as in C. What the compiler
does check: every type, every literal's range, every match's exhaustiveness,
every mutation against an immutable binding, every path's return, and every
ambiguous expression.

### Writing VIBE economically

The shortest correct form is the intended one: leave out parentheses a level
does not need, let bindings infer their type (`$~ i = 0`), count with
`* i 0 n { }`, update with `+=`, and clean up with `~`.

---

## 15. A complete program

```
; count primes below a limit and print the total
<<"std.vibe"

$$ LIMIT s64 = 1000000

@ count (n s64) s64 {
  $ p *u8 = mm(n + 1)
  ? p == *u8(0) {
    ^ -1
  }
  ~ mu(p, n + 1)
  $~ c = 0
  * i 2 (n + 1) {
    ? p[i] == 0 {
      c += 1
      $~ j = i * i
      * j <= n {
        p[j] = 1
        j += i
      }
    }
  }
  ^ c
}

@! () s64 {
  ps("primes below ")
  pn(LIMIT)
  ps(": ")
  pnl(count(LIMIT))
  ^ 0
}
```
