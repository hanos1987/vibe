"""VIBE C backend: IR to freestanding C, for an optimising C compiler.

The native backend needs nothing but Python. This one trades that for the
decades of optimisation in gcc/clang: the same IR is printed as C, one
variable per virtual register, and compiled with -O3 (add VIBE_CFLAGS=-march=native to tune for the host). The
result is still a static executable with no libc and no runtime; the entry
stub, the syscalls and the inline machine code are the same as native.
"""

import os
import shutil
import subprocess
import tempfile

from .opt import prune

PRELUDE = r"""
typedef signed char s8; typedef short s16; typedef int s32; typedef long long s64;
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;
typedef unsigned long long u64;
typedef struct { s8 x; } __attribute__((packed, may_alias)) m_s8;
typedef struct { u8 x; } __attribute__((packed, may_alias)) m_u8;
typedef struct { s16 x; } __attribute__((packed, may_alias)) m_s16;
typedef struct { u16 x; } __attribute__((packed, may_alias)) m_u16;
typedef struct { s32 x; } __attribute__((packed, may_alias)) m_s32;
typedef struct { u32 x; } __attribute__((packed, may_alias)) m_u32;
typedef struct { s64 x; } __attribute__((packed, may_alias)) m_s64;
typedef struct { u64 x; } __attribute__((packed, may_alias)) m_u64;
typedef struct { float x; } __attribute__((packed, may_alias)) m_f32;
typedef struct { double x; } __attribute__((packed, may_alias)) m_f64;
void *memcpy(void *d, const void *s, unsigned long n) {
  u8 *a = d; const u8 *b = s; while (n--) *a++ = *b++; return d; }
void *memmove(void *d, const void *s, unsigned long n) {
  u8 *a = d; const u8 *b = s;
  if (a < b) while (n--) *a++ = *b++; else while (n--) a[n] = b[n];
  return d; }
void *memset(void *d, int c, unsigned long n) {
  u8 *a = d; while (n--) *a++ = (u8)c; return d; }
int memcmp(const void *x, const void *y, unsigned long n) {
  const u8 *a = x, *b = y;
  for (; n--; a++, b++) if (*a != *b) return *a - *b;
  return 0; }
static __attribute__((noinline)) s64 vibe_clone(s64 fn, s64 arg, s64 top, s64 tid) {
  s64 *sp = (s64*)top; sp[-2] = fn; sp[-1] = arg;
  register s64 rax __asm__("rax") = 56;
  register s64 rdi __asm__("rdi") = 0x350F00; register s64 rsi __asm__("rsi") = (s64)(sp - 2);
  register s64 rdx __asm__("rdx") = tid; register s64 r10 __asm__("r10") = tid;
  register s64 r8 __asm__("r8") = 0;
  s64 ret;
  __asm__ volatile("syscall\n\ttest %%rax, %%rax\n\tjnz 1f\n\tpop %%rax\n\tpop %%rdi\n"
      "\tcall *%%rax\n\txor %%edi, %%edi\n\tmov $60, %%eax\n\tsyscall\n1:" : "=a"(ret)
      : "a"(rax), "r"(rdi), "r"(rsi), "r"(rdx), "r"(r10), "r"(r8) : "rcx", "r11", "memory");
  return ret; }
static inline s64 vibe_f2i(double x) {
  return (x >= -0x1p63 && x < 0x1p63) ? (s64)x : (s64)(1ULL << 63); }
static inline s64 vibe_f2u(double x) {
  if (!(x >= 0)) return vibe_f2i(x);
  return (x < 0x1p64) ? (s64)(u64)x : (s64)(1ULL << 63); }
static inline s64 vibe_bits(double d) { s64 r; __builtin_memcpy(&r, &d, 8); return r; }
static inline double vibe_fbits(s64 x) { double d; __builtin_memcpy(&d, &x, 8); return d; }
static inline __attribute__((always_inline))
s64 vibe_sys(s64 n, s64 a, s64 b, s64 c, s64 d, s64 e, s64 f) {
  register s64 rax __asm__("rax") = n;
  register s64 rdi __asm__("rdi") = a; register s64 rsi __asm__("rsi") = b;
  register s64 rdx __asm__("rdx") = c; register s64 r10 __asm__("r10") = d;
  register s64 r8 __asm__("r8") = e; register s64 r9 __asm__("r9") = f;
  s64 ret;
  __asm__ volatile("syscall" : "=a"(ret)
      : "a"(rax), "r"(rdi), "r"(rsi), "r"(rdx), "r"(r10), "r"(r8), "r"(r9)
      : "rcx", "r11", "memory");
  return ret; }
"""

ENTRY = r"""
__asm__(".globl _start\n_start:\n"
        "  mov %rsp, SPSYM(%rip)\n"
        "  call vibe_entry\n"
        "  mov %eax, %edi\n  mov $231, %eax\n  syscall\n  ud2\n");
"""

CFLAGS = ["-O3", "-fno-math-errno", "-mpopcnt", "-static", "-nostdlib", "-ffreestanding",
          "-fno-stack-protector", "-fno-strict-aliasing", "-fwrapv",
          "-fno-tree-loop-distribute-patterns", "-fno-pie", "-no-pie",
          "-fno-asynchronous-unwind-tables", "-w", "-s",
          "-Wl,--build-id=none"]


def mangle(name):
    out = []
    for ch in name:
        if ch.isascii() and (ch.isalnum()):
            out.append(ch)
        else:
            out.append("_%x_" % ord(ch) if ch != "_" else "__")
    return "".join(out)


def fn_name(name):
    return "vibe_entry" if name == "@!" else "f_" + mangle(name)


def narrow(expr, ty):
    if ty is None:
        return expr
    if ty.kind == "bool":
        return "(s64)(u8)(%s)" % expr
    if ty.kind != "int" or ty.size == 8:
        return expr
    return "(s64)(%s%d)(%s)" % ("s" if ty.signed else "u", ty.size * 8, expr)


def mem(addr, size, signed, isf):
    if isf:
        t = "m_f%d" % (size * 8)
    else:
        t = "m_%s%d" % ("s" if signed else "u", size * 8)
    return "((%s*)(%s))->x" % (t, addr)


def ctype(t):
    if t.kind == "float":
        return "float" if t.bits == 32 else "double"
    if t.kind == "int":
        return "%s%d" % ("s" if t.signed else "u", t.size * 8)
    if t.kind == "bool":
        return "u8"
    if t.kind == "void":
        return "void"
    return "void*"


def fsig(argf, retf):
    return "%s(*)(%s)" % ("double" if retf else "s64",
                          ", ".join("double" if x else "s64" for x in argf)
                          or "void")


class CGen:
    def __init__(self, prog):
        self.prog = prog
        self.out = []

    def run(self):
        prune(self.prog)
        o = self.out
        o.append(PRELUDE)
        for lbl, (size, align, init) in self.prog.globals.items():
            body = ""
            if init is not None:
                body = " = {%s}" % ",".join(str(b) for b in init)
            o.append("static u8 g_%s[%d] __attribute__((aligned(%d), used))%s;"
                     % (mangle(lbl), max(size, 1), max(align, 1), body))
        for lbl, blob in self.prog.rodata:
            o.append("static const u8 g_%s[%d] __attribute__((aligned(8))) = {%s};"
                     % (mangle(lbl), max(len(blob), 1),
                        ",".join(str(b) for b in blob)))
        for f in self.prog.funcs:
            o.append(self.proto(f) + ";")
        for name, (lib, ps, rt, variadic, csym) in self.prog.externs.items():
            args = [ctype(t) for t in ps] + (["..."] if variadic else [])
            o.append("extern %s %s(%s);" % (ctype(rt), csym,
                                            ", ".join(args) or "void"))
        if self.prog.externs:
            # hosted: the C runtime owns _start; recover the kernel's stack
            # block (argc sits just below argv) for argc/arg/env
            o.append("int main(int argc, char **argv) {\n"
                     "  *(s64*)g_%s = (s64)((s64*)argv - 1);\n"
                     "  return (int)vibe_entry();\n}" % mangle("$g___sp"))
        else:
            o.append(ENTRY.replace("SPSYM", "g_" + mangle("$g___sp")))
        for f in self.prog.funcs:
            self.func(f)
        return "\n".join(o) + "\n"

    def proto(self, f):
        ps = ", ".join("%s v%d" % ("double" if pty.kind == "float" else "s64", pv)
                       for (_, pty, pv) in f.params) or "void"
        rt = "double" if f.ret.kind == "float" else "s64"
        link = "" if f.name == "@!" else "static "
        return "%s%s %s(%s)" % (link, rt, fn_name(f.name), ps)

    def func(self, f):
        o = self.out
        self.f = f
        o.append(self.proto(f) + " {")
        pvs = set(pv for (_, _, pv) in f.params)
        ints = [v for v in range(f.nvreg)
                if v not in pvs and v not in f.float_vregs]
        flts = [v for v in range(f.nvreg)
                if v not in pvs and v in f.float_vregs]
        if ints:
            o.append("  s64 %s;" % ", ".join("v%d = 0" % v for v in ints))
        if flts:
            o.append("  double %s;" % ", ".join("v%d = 0" % v for v in flts))
        for s in f.slots:
            o.append("  u8 sl%d[%d] __attribute__((aligned(%d)));"
                     % (s.idx, max(s.size, 1), max(s.align, 1)))
        for ins in f.ins:
            self.ins(ins)
        o.append("  __builtin_trap();")
        o.append("}")

    def lab(self, name):
        return "L_" + mangle(name)

    def ins(self, i):
        o = self.out
        op = i.op
        f = self.f
        if op == "label":
            o.append("%s: ;" % self.lab(i.a))
        elif op == "const":
            v = i.b & 0xFFFFFFFFFFFFFFFF
            o.append("  v%d = (s64)0x%xULL;" % (i.a, v))
        elif op == "fconst":
            x = float(i.b)
            if x != x:
                lit = "__builtin_nan(\"\")"
            elif x in (float("inf"), float("-inf")):
                lit = "%s__builtin_inf()" % ("-" if x < 0 else "")
            else:
                lit = x.hex()
            if i.c == 32:
                lit = "(double)(float)%s" % lit
            o.append("  v%d = %s;" % (i.a, lit))
        elif op == "mov":
            o.append("  v%d = v%d;" % (i.a, i.b))
        elif op == "lea":
            o.append("  v%d = (s64)sl%d;" % (i.a, i.b.idx))
        elif op == "leaf":
            o.append("  v%d = (s64)&%s;" % (i.a, fn_name(i.b)))
        elif op in ("leag", "leas"):
            o.append("  v%d = (s64)g_%s;" % (i.a, mangle(i.b)))
        elif op == "bin":
            self.bin(i)
        elif op == "un":
            o.append("  v%d = %s;" % (i.a, narrow(
                "(s64)(%s(u64)v%d)" % (i.b, i.c), i.d)))
        elif op == "cmp":
            c = "s64" if i.e else "u64"
            o.append("  v%d = ((%s)v%d %s (%s)v%d);" % (i.a, c, i.c, i.b, c, i.d))
        elif op == "fcmp":
            o.append("  v%d = (v%d %s v%d);" % (i.a, i.c, i.b, i.d))
        elif op == "fbin":
            if i.e == 32:
                o.append("  v%d = (double)((float)v%d %s (float)v%d);"
                         % (i.a, i.c, i.b, i.d))
            else:
                o.append("  v%d = v%d %s v%d;" % (i.a, i.c, i.b, i.d))
        elif op == "fun":
            o.append("  v%d = -v%d;" % (i.a, i.c))
        elif op == "load":
            m = mem("v%d" % i.b, i.c, i.d, i.e)
            o.append("  v%d = %s;" % (i.a, m))
        elif op == "store":
            m = mem("v%d" % i.a, i.c, False, i.d)
            o.append("  %s = v%d;" % (m, i.b))
        elif op == "memcpy":
            if i.c:
                o.append("  __builtin_memmove((void*)v%d, (void*)v%d, %d);"
                         % (i.a, i.b, i.c))
        elif op == "memzero":
            if i.b:
                o.append("  __builtin_memset((void*)v%d, 0, %d);" % (i.a, i.b))
        elif op == "jmp":
            o.append("  goto %s;" % self.lab(i.a))
        elif op == "br":
            o.append("  if (v%d) goto %s; else goto %s;"
                     % (i.a, self.lab(i.b), self.lab(i.c)))
        elif op == "ret":
            o.append("  return %s;" % ("0" if i.a is None else "v%d" % i.a))
        elif op in ("call", "calli"):
            args = ", ".join("v%d" % v for v in i.c)
            ext = self.prog.externs.get(i.b) if op == "call" else None
            if ext is not None:
                ps = ext[1]
                parts = []
                for k, v in enumerate(i.c):
                    if k < len(ps):
                        parts.append("(%s)v%d" % (ctype(ps[k]), v))
                    else:
                        parts.append("v%d" % v)
                call = "%s(%s)" % (ext[4], ", ".join(parts))
                if i.a is None:
                    o.append("  %s;" % call)
                else:
                    o.append("  v%d = (%s)%s;" % (
                        i.a, "double" if i.e else "s64", call))
                return
            if op == "call":
                callee = fn_name(i.b)
            else:
                callee = "((%s)v%d)" % (fsig(i.d, i.e), i.b)
            dst = "" if i.a is None else "v%d = " % i.a
            o.append("  %s%s(%s);" % (dst, callee, args))
        elif op == "syscall":
            args = ["v%d" % v for v in i.c] + ["0"] * (6 - len(i.c))
            o.append("  v%d = vibe_sys(%d, %s);" % (i.a, i.b, ", ".join(args)))
        elif op == "cvt":
            self.cvt(i)
        elif op == "intr":
            x = ["v%d" % v for v in i.c]
            e = {
                "sqrt": lambda: ("(double)__builtin_sqrtf((float)%s)" if i.e == 32
                                 else "__builtin_sqrt(%s)") % x[0],
                "bits": lambda: "vibe_bits(%s)" % x[0],
                "fbits": lambda: "vibe_fbits(%s)" % x[0],
                "popcnt": lambda: "__builtin_popcountll(%s)" % x[0],
                "clz": lambda: "(%s ? __builtin_clzll(%s) : 64)" % (x[0], x[0]),
                "ctz": lambda: "(%s ? __builtin_ctzll(%s) : 64)" % (x[0], x[0]),
                "bswap": lambda: "(s64)__builtin_bswap64((u64)%s)" % x[0],
                "rdtsc": lambda: "(s64)__builtin_ia32_rdtsc()",
                "pause": lambda: "__builtin_ia32_pause()",
                "cas": lambda: "__sync_bool_compare_and_swap((s64*)%s, %s, %s)"
                               % tuple(x),
                "clone": lambda: "vibe_clone(%s, %s, %s, %s)" % tuple(x),
                "load": lambda: "*(volatile s64*)%s" % x[0],
                "store": lambda: "*(volatile s64*)%s = %s" % tuple(x),
                "xadd": lambda: "__sync_fetch_and_add((s64*)%s, %s)" % tuple(x),
            }[i.b]()
            # a data race is undefined in C, so the optimiser would happily
            # move ordinary loads and stores across a lock. An empty asm
            # block that "clobbers memory" pins them on their side of it.
            fence = i.b in ("cas", "xadd", "load", "store")
            if fence:
                o.append("  __asm__ volatile(\"\" : : : \"memory\");")
            o.append("  %s%s;" % ("" if i.a is None else "v%d = " % i.a, e))
            if fence:
                o.append("  __asm__ volatile(\"\" : : : \"memory\");")
        elif op == "rawbytes":
            o.append("  __asm__ volatile(\".byte %s\");"
                     % ",".join(str(b) for b in i.a))
        elif op == "trap":
            o.append("  __builtin_trap();")
        else:
            raise Exception("C backend: unhandled IR op %r" % op)

    def bin(self, i):
        d, o, x, y, ty = i.a, i.b, i.c, i.d, i.e
        signed = ty is not None and ty.kind == "int" and ty.signed
        if o in ("/", "%"):
            c = "s64" if signed else "u64"
            e = "(s64)((%s)v%d %s (%s)v%d)" % (c, x, o, c, y)
        elif o == "<<":
            e = "(s64)((u64)v%d << (v%d & 63))" % (x, y)
        elif o == ">>":
            c = "s64" if signed else "u64"
            e = "(s64)((%s)v%d >> (v%d & 63))" % (c, x, y)
        else:
            e = "(s64)((u64)v%d %s (u64)v%d)" % (x, o, y)
        self.out.append("  v%d = %s;" % (d, narrow(e, ty)))

    def cvt(self, i):
        d, s, ft, tt = i.a, i.b, i.c, i.d
        if ft.kind == "float" and tt.kind == "float":
            e = "(double)(float)v%d" % s if tt.bits == 32 else "v%d" % s
        elif ft.kind == "float":
            # out of range (or NaN) gives the most negative s64, which is
            # what the hardware conversion the native backend uses gives
            if tt.kind == "int" and not tt.signed and tt.size == 8:
                e = "vibe_f2u(v%d)" % s
            else:
                e = narrow("vibe_f2i(v%d)" % s, tt)
        elif tt.kind == "float":
            src = "(u64)v%d" % s if (ft.kind == "int" and not ft.signed
                                    and ft.size == 8) else "v%d" % s
            e = "(double)%s" % src
            if tt.bits == 32:
                e = "(double)(float)%s" % src
        else:
            e = narrow("v%d" % s, tt)
        self.out.append("  v%d = %s;" % (d, e))


def find_cc():
    for cand in (os.environ.get("VIBE_CC"), "gcc", "clang", "cc"):
        if cand and shutil.which(cand):
            return cand
    return None


def emit_c(prog):
    return CGen(prog).run()


def compile_program_c(prog, keep=None):
    """Return the bytes of a static executable built through the C compiler."""
    cc = find_cc()
    if cc is None:
        raise RuntimeError("the C backend needs gcc or clang on PATH "
                           "(or set VIBE_CC)")
    src = emit_c(prog)
    if keep:
        with open(keep, "w") as fh:
            fh.write(src)
    tmp = tempfile.mkdtemp(prefix="vibe-c-")
    try:
        cpath = os.path.join(tmp, "out.c")
        bpath = os.path.join(tmp, "out")
        with open(cpath, "w") as fh:
            fh.write(src)
        extra = os.environ.get("VIBE_CFLAGS", "").split()
        flags = list(CFLAGS)
        libs = []
        if prog.externs:
            for drop in ("-static", "-nostdlib", "-ffreestanding",
                         "-fno-pie", "-no-pie"):
                flags.remove(drop)
            for (lib, _, _, _, _) in prog.externs.values():
                if lib not in ("c", "") and "-l" + lib not in libs:
                    libs.append("-l" + lib)
        r = subprocess.run([cc] + flags + extra + [cpath, "-o", bpath] + libs,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("C compiler failed:\n" + r.stderr)
        with open(bpath, "rb") as fh:
            return fh.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
