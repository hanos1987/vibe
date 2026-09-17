"""fuzz4: differential fuzzer -O vs -O0 vs C backend, richer feature set.
usage: fuzz4.py A B [outdir]"""
import random, sys, os, subprocess
sys.dont_write_bytecode = True
ROOT = os.environ.get("VIBEROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from vibelang.front import build
from vibelang.codegen import compile_program
from vibelang.cback import compile_program_c
from vibelang.cli import stdlib_dir
USEC = os.environ.get("NOC") is None
ITYPES = ["s64", "u64", "s32", "u32", "s16", "u16", "s8", "u8"]
FTYPES = ["f64", "f32"]
BITS = {"s64": 64, "u64": 64, "s32": 32, "u32": 32, "s16": 16, "u16": 16, "s8": 8, "u8": 8}

PRE = '''<<"std.vibe"
%P { a s64, b u8, c f64, d s16 }
%Q { p %P, arr [3]s32, f f32 }
%| S { |A(s64) |B(f64, u8) |C(%P) |D }
%Box<T> { v T, w T }
$~ arr [16]s64
$~ gh s64 = 0
@ clamp (x f64) f64 {
  ? x > -1000000000.0 {
    ? x < 1000000000.0 {
      ^ x
    }
  }
  ^ 0.0
}
@ fh (x f64) s64 {
  ^ s64(\\bits(clamp(x)))
}
@ gsel<T> (c b, x T, y T) T {
  ? c {
    ^ x
  }
  ^ y
}
@ gbox<T> (x T, y T) %Box<T> {
  ^ %Box{ v: y, w: x }
}
@ mkp (a s64, b u8, c f64, d s16) %P {
  ^ %P{ a: a, b: b, c: c, d: d }
}
@ sumq (q %Q) s64 {
  $~ t = q.p.a + s64(q.p.b) + s64(q.p.d) + fh(q.p.c) + fh(f64(q.f))
  * i 0 3 {
    t = (t * 3) + s64(q.arr[i])
  }
  ^ t
}
@ sums (s %S) s64 {
  ?? s {
    |A(x) { ^ x }
    |B(f, u) { ^ fh(f) + s64(u) }
    |C(p) { ^ p.a + s64(p.d) }
    |D { ^ 77 }
  }
  ^ 0
}
'''


def lit(t, r):
    if t in FTYPES:
        v = r.choice(["0.0", "1.0", "0.5", "-2.25", "3.75", "1e10", "0.1", "%d.%d" % (r.randint(0, 999), r.randint(0, 99))])
        return v if t == "f64" else "f32(%s)" % v
    b = BITS[t]
    hi = (1 << (b - (1 if t[0] == "s" else 0))) - 1
    v = str(r.choice([0, 1, 2, 3, 7, hi, hi - 1, r.randint(0, hi), r.randint(0, min(hi, 300))]))
    return v if t == "s64" else "%s(%s)" % (t, v)


class G:
    def __init__(s, r, sigs=None):
        s.r = r; s.vars = {}; s.n = 0; s.lines = []; s.ind = 1; s.depth = 0
        s.sigs = sigs or []; s.inloop = 0; s.retty = None; s.structs = {}

    def emit(s, l): s.lines.append("  " * s.ind + l)

    def expr(s, t, d=0):
        r = s.r
        cands = [v for v, (vt, _) in s.vars.items() if vt == t]
        k = r.random()
        if d > 3 or k < 0.25:
            if cands and r.random() < 0.7: return r.choice(cands)
            if t == "s64" and s.structs and r.random() < 0.3:
                n, ty = r.choice(list(s.structs.items()))
                if ty == "P": return "%s.a" % n
                if ty == "Q": return "%s.p.a" % n
            return lit(t, r)
        if t in FTYPES:
            if k < 0.35:
                t2 = r.choice(["s64", "s32", "u8", "s16", "u32"] + FTYPES)
                if t2 != t: return "%s(%s)" % (t, s.expr(t2, d + 1))
            if k < 0.42: return "-(%s)" % s.expr(t, d + 1)
            if k < 0.48: return "\\sqrt(%s)" % s.expr(t, d + 1)
            if k < 0.55 and t == "f64" and s.structs:
                n, ty = r.choice(list(s.structs.items()))
                if ty == "P": return "%s.c" % n
                if ty == "Q": return "f64(%s.f)" % n
            if k < 0.62:
                return "gsel<%s>(%s, %s, %s)" % (t, s.cond(d + 1), s.expr(t, d + 1), s.expr(t, d + 1))
            fs = [i for i, sg in enumerate(s.sigs) if sg[0] == t]
            if fs and r.random() < 0.3: return s.call(r.choice(fs), d)
            op = r.choice(["+", "-", "*", "/"])
            return "(%s %s %s)" % (s.expr(t, d + 1), op, s.expr(t, d + 1))
        if k < 0.33:
            t2 = r.choice(ITYPES)
            if t2 != t: return "%s(%s)" % (t, s.expr(t2, d + 1))
        if k < 0.36:
            ft = r.choice(FTYPES)
            return "%s(clamp(%s))" % (t, s.expr(ft, d + 1) if ft == "f64" else "f64(%s)" % s.expr(ft, d + 1))
        if k < 0.42: return "-(%s)" % s.expr(t, d + 1)
        if k < 0.46: return "~(%s)" % s.expr(t, d + 1)
        if k < 0.50:
            return ("%s(s64(%s))" % (t, s.cond(d + 1))) if t != "s64" else "s64(%s)" % s.cond(d + 1)
        if k < 0.54 and t == "s64":
            return "arr[(%s & 15)]" % s.expr("s64", d + 1)
        if k < 0.57 and t == "u64":
            return "%s(%s)" % (r.choice(["\\popcnt", "\\clz", "\\ctz", "\\bswap"]), s.expr(t, d + 1))
        if k < 0.60:
            return "gsel<%s>(%s, %s, %s)" % (t, s.cond(d + 1), s.expr(t, d + 1), s.expr(t, d + 1))
        if k < 0.63:
            return "gbox<%s>(%s, %s).%s" % (t, s.expr(t, d + 1), s.expr(t, d + 1), r.choice("vw"))
        if k < 0.66 and t == "s64":
            return r.choice([
                "sums(%%S|A(%s))" % s.expr("s64", d + 1),
                "sums(%%S|B(%s, %s))" % (s.expr("f64", d + 1), s.expr("u8", d + 1)),
                "sums(%%S|C(mkp(%s, %s, %s, %s)))" % (s.expr("s64", d + 1), s.expr("u8", d + 1), s.expr("f64", d + 1), s.expr("s16", d + 1)),
                "sums(%S|D)", "fh(%s)" % s.expr("f64", d + 1)])
        if k < 0.69 and t == "s64" and s.structs:
            qs = [n for n, ty in s.structs.items() if ty == "Q"]
            if qs: return "sumq(%s)" % r.choice(qs)
        fs = [i for i, sg in enumerate(s.sigs) if sg[0] == t]
        if fs and r.random() < 0.3: return s.call(r.choice(fs), d)
        op = r.choice(["+", "-", "*", "&", "|", "^", "<<", ">>", "/", "%", "+", "-", "*"])
        a = s.expr(t, d + 1); b = s.expr(t, d + 1)
        if op in ("/", "%"): b = "((%s & 7) + 1)" % b
        if op in ("<<", ">>"): b = "(%s & %d)" % (b, BITS[t] - 1)
        return "(%s %s %s)" % (a, op, b)

    def call(s, i, d):
        sg = s.sigs[i]
        args = []
        for pt in sg[1]:
            if pt == "P":
                ps = [n for n, ty in s.structs.items() if ty == "P"]
                if ps and s.r.random() < 0.5: args.append(s.r.choice(ps))
                else: args.append("mkp(%s, %s, %s, %s)" % (s.expr("s64", d + 2), s.expr("u8", d + 2), s.expr("f64", d + 2), s.expr("s16", d + 2)))
            else:
                args.append(s.expr(pt, d + 1))
        return "g%d(%s)" % (i, ", ".join(args))

    def cond(s, d=0):
        r = s.r; t = r.choice(ITYPES + FTYPES)
        c = "(%s %s %s)" % (s.expr(t, d + 1), r.choice(["==", "!=", "<", "<=", ">", ">="]), s.expr(t, d + 1))
        k = r.random()
        if d < 2 and k < 0.2: return "(%s && %s)" % (c, s.cond(d + 1))
        if d < 2 and k < 0.4: return "(%s || %s)" % (c, s.cond(d + 1))
        if k < 0.5: return "!%s" % c
        return c

    def newvar(s):
        r = s.r
        k = r.random()
        n = "v%d" % s.n; s.n += 1
        if k < 0.1:
            s.emit("$~ %s %%P = mkp(%s, %s, %s, %s)" % (n, s.expr("s64"), s.expr("u8"), s.expr("f64"), s.expr("s16")))
            s.structs[n] = "P"; return
        if k < 0.17:
            ps = [x for x, ty in s.structs.items() if ty == "P"]
            pe = r.choice(ps) if ps else "mkp(1, 2, 3.0, 4)"
            s.emit("$~ %s %%Q = %%Q{ p: %s, arr: [%s, %s, %s], f: %s }" % (n, pe, s.expr("s32"), s.expr("s32"), s.expr("s32"), s.expr("f32")))
            s.structs[n] = "Q"; return
        t = r.choice(ITYPES + FTYPES)
        s.emit("$~ %s %s = %s" % (n, t, s.expr(t))); s.vars[n] = (t, True)

    def hashv(s, v, t):
        if t == "s64": return v
        if t == "f64": return "fh(%s)" % v
        if t == "f32": return "fh(f64(%s))" % v
        return "s64(%s)" % v

    def stmt(s):
        r = s.r; k = r.random()
        muts = [v for v, (t, m) in s.vars.items() if m]
        if k < 0.2 or not muts: s.newvar(); return
        if k < 0.4:
            v = r.choice(muts); s.emit("%s = %s" % (v, s.expr(s.vars[v][0]))); return
        if k < 0.5:
            v = r.choice(muts); t = s.vars[v][0]
            if t in FTYPES:
                s.emit("%s %s= %s" % (v, r.choice("+-*"), s.expr(t)))
            else:
                op = r.choice(["+", "-", "*", "&", "|", "^", "<<", ">>", "/"])
                e = s.expr(t)
                if op == "/": e = "((%s & 7) + 1)" % e
                if op in ("<<", ">>"): e = "(%s & %d)" % (e, BITS[t] - 1)
                s.emit("%s %s= %s" % (v, op, e))
            return
        if k < 0.56:
            if r.random() < 0.5: s.emit("arr[(%s & 15)] = %s" % (s.expr("s64"), s.expr("s64")))
            else: s.emit("arr[(h & 15)] %s %s" % (r.choice(["+=", "^="]), s.expr("s64")))
            return
        if k < 0.62 and s.structs:
            n, ty = r.choice(list(s.structs.items()))
            if ty == "P":
                f, t = r.choice([("a", "s64"), ("b", "u8"), ("c", "f64"), ("d", "s16")])
                s.emit("%s.%s %s %s" % (n, f, r.choice(["=", "+=", "-="]), s.expr(t)))
            else:
                ch = r.random()
                if ch < 0.4: s.emit("%s.arr[(h & 1)] += %s" % (n, s.expr("s32")))
                elif ch < 0.7: s.emit("%s.p.d ^= %s" % (n, s.expr("s16")))
                else:
                    ps = [x for x, ty2 in s.structs.items() if ty2 == "P"]
                    if ps: s.emit("%s.p = %s" % (n, r.choice(ps)))
                    else: s.emit("%s.f *= %s" % (n, s.expr("f32")))
            return
        if k < 0.68:
            v = r.choice(list(s.vars)); s.emit("h = ((h * 31) + %s)" % s.hashv(v, s.vars[v][0])); return
        if k < 0.72:
            s.emit("~ gh = ((gh * 7) + %s)" % s.expr("s64")); return
        if k < 0.75 and s.retty and s.depth > 0:
            s.emit("? %s {" % s.cond()); s.emit("  ^ %s" % s.expr(s.retty)); s.emit("}"); return
        if s.depth >= 3: s.newvar(); return
        saved = dict(s.vars); ssaved = dict(s.structs)
        if k < 0.87:
            s.emit("? %s {" % s.cond()); s.ind += 1; s.depth += 1
            for _ in range(r.randint(1, 4)): s.stmt()
            s.ind -= 1; s.vars = dict(saved); s.structs = dict(ssaved)
            if r.random() < 0.5:
                s.emit("}"); s.emit(": {"); s.ind += 1
                for _ in range(r.randint(1, 3)): s.stmt()
                s.ind -= 1; s.vars = dict(saved); s.structs = dict(ssaved)
            s.emit("}"); s.depth -= 1
        else:
            c = "c%d" % s.n; s.n += 1
            if r.random() < 0.5:
                ct = r.choice(["s64", "u8", "s32", "u16"])
                lo = r.randint(0, 3); hi = r.randint(0, 7)
                s.emit("$ e%s %s = %d" % (c, ct, hi))
                s.emit("* %s %d e%s {" % (c, lo, c))
                s.ind += 1; s.depth += 1
            else:
                ct = "s64"
                s.emit("$~ %s s64 = 0" % c)
                s.emit("* (%s < %d) {" % (c, r.randint(1, 6))); s.ind += 1; s.depth += 1
                s.emit("%s += 1" % c)
            s.vars[c] = (ct, False)
            for _ in range(r.randint(1, 5)):
                s.stmt()
                if r.random() < 0.12:
                    s.emit("? %s {" % s.cond()); s.emit("  " + r.choice(["*<", "*>"])); s.emit("}")
            s.ind -= 1; s.vars = dict(saved); s.structs = dict(ssaved)
            s.emit("}"); s.depth -= 1


def helpers(r):
    out = []; sigs = []
    for k in range(5):
        rt = r.choice(ITYPES + FTYPES)
        np = r.choice([1, 2, 3, 7, 9, 12])
        pts = [r.choice(ITYPES + FTYPES + ["P"]) for _ in range(np)]
        g = G(r, list(sigs) if r.random() < 0.6 else []); g.retty = rt
        for i, pt in enumerate(pts):
            if pt == "P": g.structs["a%d" % i] = "P"
            else: g.vars["a%d" % i] = (pt, True)
        if r.random() < 0.5:
            g.emit("$~ loc [4]s64")
            g.emit("* li 0 4 {"); g.emit("  loc[li] = (h + li)"); g.emit("}")
            g.emit("h += loc[(h & 3)]")
        for _ in range(r.randint(0, 4)): g.stmt()
        body = "\n".join(g.lines)
        ps = ", ".join("a%d %s" % (i, ("%P" if pt == "P" else pt)) for i, pt in enumerate(pts))
        hx = " ^ ".join(["%s(h)" % rt if rt != "s64" else "h"]) if rt in ITYPES else "%s(h & 1023)" % rt
        out.append("@ g%d (%s) %s {\n  $~ h s64 = 1\n%s\n  ^ (%s + %s)\n}" % (k, ps, rt, body, g.expr(rt), hx)
                   if rt in FTYPES else
                   "@ g%d (%s) %s {\n  $~ h s64 = 1\n%s\n  ^ (%s ^ %s)\n}" % (k, ps, rt, body, g.expr(rt), hx))
        sigs.append((rt, pts))
    return "\n".join(out), sigs


def gen(seed):
    r = random.Random(seed); hs, sigs = helpers(r); g = G(r, sigs); g.retty = "s64"
    g.vars = {"p0": ("s64", True), "p1": ("u32", True), "p2": ("f64", True), "p3": ("u8", True)}
    for _ in range(r.randint(5, 25)): g.stmt()
    for v, (t, _) in list(g.vars.items()):
        g.emit("h = ((h * 31) + %s)" % g.hashv(v, t))
    for n, ty in g.structs.items():
        g.emit("h = ((h * 31) + %s)" % ("sumq(%s)" % n if ty == "Q" else "sums(%%S|C(%s))" % n))
    body = "\n".join(g.lines)
    return PRE + '''%s
@ f (p0 s64, p1 u32, p2 f64, p3 u8) s64 {
  $~ h s64 = 7
%s
  * k 0 16 {
    h = ((h * 31) + arr[k])
  }
  ^ h
}
@! () s64 {
  px(u64(f(3, 4000000000, 1.5, 200)))
  nl()
  px(u64(gh))
  nl()
  px(u64(f((0 - 77), 5, -0.125, 0)))
  nl()
  px(u64(gh))
  nl()
  ^ 0
}
''' % (hs, body)


def run(path, mode):
    prog = build(path, include_dirs=[stdlib_dir()])
    if mode == "c": blob = compile_program_c(prog)
    else: blob = compile_program(prog, mode == "o1")
    out = path + "." + mode
    open(out, "wb").write(blob); os.chmod(out, 0o755)
    p = subprocess.run([out], capture_output=True, timeout=10)
    return p.returncode, p.stdout


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    od = sys.argv[3] if len(sys.argv) > 3 else "fz4"
    os.makedirs(od, exist_ok=True)
    bad = 0
    for seed in range(a, b):
        src = gen(seed); path = "%s/s%d.vibe" % (od, seed)
        open(path, "w").write(src)
        try:
            rs = [run(path, m) for m in (["o1", "o0", "c"] if USEC else ["o1", "o0"])]
        except Exception as e:
            print("seed", seed, "EXC", type(e).__name__, str(e)[:300].replace("\n", " | ")); bad += 1; sys.stdout.flush(); continue
        if any(x != rs[0] for x in rs):
            print("seed", seed, "MISMATCH", rs); bad += 1
        else:
            for m in ("", ".o1", ".o0", ".c"):
                try: os.remove(path + m)
                except OSError: pass
        sys.stdout.flush()
    print("done bad=", bad)
