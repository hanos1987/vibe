# VIBE — Language Specification v0.1

VIBE is a systems language with **no natural-language keywords**. Every
construct is a sigil. It compiles straight to x86-64 machine code: `vibec`
writes the ELF bytes itself, with no assembler, no linker, no C library and
no runtime.

It is designed to be written by a model. The three rules below exist because
they remove the ambiguities that generated code gets wrong most often.

**Rule 1 — There is no operator precedence.**
`(1 + 2 * 3)` is a compile error. Write `(1 + (2 * 3))`. Every mixed-operator
expression must be parenthesised, so an expression means exactly what its
shape says.

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
| `^` | return (bare `^` returns from a `v` function) | `^ x` |
| `?` `:` | if / else | `? c { } : { }` |
| `??` `\|` | match / arm | `?? r { \|Ok(v) { } \|Err { } }` |
| `_` | wildcard arm (must be last) | `\|_ { }` |
| `*` | loop while | `* (i < n) { }` |
| `*<` | break | `*<` |
| `*>` | continue | `*>` |
| `\N` | syscall number N | `\1(1, p, n)` |
| `\\[..]` | inline machine code bytes | `\\[0x90]` |
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

A global initialiser must be a compile-time constant, and only scalar
globals may have one; aggregates start zeroed. `$$` constants are inlined at
every use, have no address, and may be built from other `$$` constants and
from `#T`.

Functions take at most 6 parameters in v0.1.

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
*<                       ; break
*>                       ; continue

?? subject { |A(x) { } |B { } }     ; match

f(1, 2)                  ; call as a statement
\1(1, s.p, s.n)          ; syscall as a statement
\\[0x0f, 0x05]           ; raw machine code bytes
```

A binding is visible from its line to the end of the enclosing block. Inner
blocks may not shadow a name bound in the same block.

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
(1 + (2 * 3))        ; fine
(1 + 2 + 3)          ; fine: a chain of one associative operator
(1 + 2 * 3)          ; error: mixed operators need parentheses
(a < b < c)          ; error: comparisons never chain
```

### Conversions

None are implicit. Both sides of a binary operator must already have the
same type. Use a cast:

```
$ a s64 = 1
$ b s32 = 2
$ c s64 = (a + s64(b))
```

Two exceptions, both safe and unambiguous:

* An integer **literal** takes the type it is used at: `$ x u8 = 200`.
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
count must equal the variant's payload count. Binders are immutable and
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

## 8. Standard library

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

## 9. Using the compiler

```
vibec prog.vibe -o prog     compile to a static executable
vibec prog.vibe --run       compile and run
vibec prog.vibe --ir        print the mid-level IR
vibec prog.vibe -O0 ...     no optimisation, no register allocation
```

The output is a static ELF64 executable that runs on Linux x86-64 with no
shared libraries. `-O0` compiles through a separate path where every value
lives in memory; it exists so any program can be run two ways and compared.

---

## 10. Grammar

```
unit     := decl*
decl     := include | fn | struct | sum | global
include  := '<<' STRING NL
fn       := ('@' IDENT | '@!') '(' params? ')' type block NL
params   := IDENT type (',' IDENT type)*
struct   := '%' IDENT '{' (IDENT type ','?)* '}' NL
sum      := '%|' IDENT '{' ('|' IDENT ('(' type (',' type)* ')')? ','?)* '}' NL
global   := ('$' | '$~' | '$$') IDENT type ('=' expr)? NL

type     := 's8'|'s16'|'s32'|'s64'|'u8'|'u16'|'u32'|'u64'
          | 'f32'|'f64'|'b'|'v'
          | '*' type | '[' INT ']' type | '%' IDENT
          | '@' '(' (type (',' type)*)? ')' type

block    := '{' NL stmt* '}'
stmt     := ('$'|'$~') IDENT (type)? ('=' expr)? NL
          | expr '=' expr NL
          | '^' expr? NL
          | '?' expr block (':' (block | stmt))? NL
          | '*' expr block NL
          | '*<' NL | '*>' NL
          | '??' expr '{' NL arm* '}' NL
          | '\\\\' '[' INT (',' INT)* ']' NL
          | expr NL
arm      := '|' (IDENT ('(' IDENT (',' IDENT)* ')')? | '_') block

expr     := unary (binop unary)*        -- one distinct operator per level
unary    := ('-'|'!'|'~') unary | '&' unary | '#' type | postfix
postfix  := primary ("'" | '.' IDENT | '[' expr ']' | '(' args? ')')*
primary  := INT | FLOAT | STRING | BYTE | IDENT
          | '(' expr ')'
          | '[' expr (',' expr)* ']'
          | '\\' INT '(' args? ')'
          | '%' IDENT '{' (IDENT ':' expr ','?)* '}'
          | '%' IDENT '|' IDENT ('(' args? ')')?
          | '@' IDENT
          | prim_type '(' expr ')' | '*' type '(' expr ')'
```

---

## 11. Calling convention and layout

* Scalar arguments go in `rdi, rsi, rdx, rcx, r8, r9`; floats in `xmm0`
  upward; the result is in `rax` or `xmm0`.
* Aggregates are passed by value: the caller makes a copy and passes its
  address. An aggregate return is written through a hidden first argument.
* The binary has two segments: read+execute for code and constants,
  read+write for globals. There is no interpreter and no dynamic section.

---

## 12. What v0.1 does not have

Stated plainly so nothing is inferred that is not there: no generics, no
closures (function pointers do not capture), no methods, interfaces or
overloading, no namespaces, no varargs,
more than 6 parameters, no threads (concurrency is by `fork`), no
exceptions, no garbage collector, no
bounds checking, no aggregate global initialisers, and no automatic
formatting of floats. `u64`-to-float conversion is exact only below 2^63.

Memory safety is the programmer's job, exactly as in C. What the compiler
does check: every type, every match's exhaustiveness, every mutation against
an immutable binding, and every ambiguous expression.

---

## 13. A complete program

```
; count primes below a limit and print the total
<<"std.vibe"

$$ LIMIT s64 = 1000000

@ count (n s64) s64 {
  $ p *u8 = mm((n + 1))
  ? (p == *u8(0)) {
    ^ -1
  }
  $~ i s64 = 2
  $~ c s64 = 0
  * (i <= n) {
    ? (p[i] == u8(0)) {
      c = (c + 1)
      $~ j s64 = (i * i)
      * (j <= n) {
        p[j] = 1
        j = (j + i)
      }
    }
    i = (i + 1)
  }
  mu(p, (n + 1))
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
