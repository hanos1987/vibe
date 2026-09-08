"""VIBE front end: resolve declarations, type-check, and lower to IR.

Checking and lowering happen in one walk. Aggregate values are represented by
their address; scalars live in virtual registers.
"""

import os
import struct

from . import ast_ as A
from . import ir
from .parser import parse
from .types import (VOID, BOOL, S8, S16, S32, S64, U8, U16, U32, U64, F32, F64,
                    PRIMS, ArrT, FnT, IntT, PtrT, StructT, SumT, Type)


class CheckError(Exception):
    pass


INT_BIN = {"+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>"}
CMP = {"==", "!=", "<", ">", "<=", ">="}
FLT_BIN = {"+", "-", "*", "/"}


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.names = {}

    def get(self, n):
        s = self
        while s:
            if n in s.names:
                return s.names[n]
            s = s.parent
        return None

    def put(self, n, v):
        self.names[n] = v


class Front:
    def __init__(self, include_dirs=()):
        self.prog = ir.Program()
        self.types = {}          # name -> StructT / SumT
        self.fns = {}            # name -> (FnT, ir.Func or None)
        self.globals = {}        # name -> (Type, label, mutable)
        self.constants = {}      # name -> (Type, int)  -- $$ comptime values
        self.include_dirs = list(include_dirs)
        self.seen_files = set()
        self.decls = []
        self.f = None            # current ir.Func
        self.scope = None
        self.loops = []
        self.cur_ret = VOID
        self.cur_sret = None

        # Builtin string value type.
        st = StructT("Str")
        st.layout([("p", PtrT(U8)), ("n", S64)])
        self.types["Str"] = st
        self.str_t = st

        # __sp is filled in by the entry stub with the stack pointer the
        # kernel handed us. argc, argv and envp are read from there.
        self.globals["__sp"] = (PtrT(U8), "$g___sp", False)
        self.prog.globals["$g___sp"] = (8, 8, None)

    # -- errors --------------------------------------------------------------
    def err(self, node, msg):
        raise CheckError("%s:%d:%d: %s" % (
            (getattr(node, "_file", None) or self.file), node.line, node.col, msg))

    # -- loading -------------------------------------------------------------
    def load(self, path):
        path = os.path.abspath(path)
        if path in self.seen_files:
            return
        self.seen_files.add(path)
        with open(path, "r") as fh:
            src = fh.read()
        decls = parse(src, os.path.basename(path))
        here = os.path.dirname(path)
        for d in decls:
            d._file = os.path.basename(path)
        for d in decls:
            if isinstance(d, A.Include):
                cand = [os.path.join(here, d.path)]
                cand += [os.path.join(x, d.path) for x in self.include_dirs]
                for c in cand:
                    if os.path.exists(c):
                        self.load(c)
                        break
                else:
                    raise CheckError("%s:%d: cannot find include %r" %
                                     (os.path.basename(path), d.line, d.path))
            else:
                self.decls.append((os.path.basename(path), d))

    # -- type resolution -----------------------------------------------------
    def resolve(self, t, node=None):
        if isinstance(t, A.TName):
            if t.name in PRIMS:
                return PRIMS[t.name]
            if t.name in self.types:
                return self.types[t.name]
            self.err(t, "unknown type %r" % t.name)
        if isinstance(t, A.TPtr):
            return PtrT(self.resolve(t.to))
        if isinstance(t, A.TArr):
            n = t.n
            if isinstance(n, str):
                c = self.constants.get(n)
                if c is None:
                    self.err(t, "array length %r is not a $$ constant" % n)
                n = c[1]
            if n <= 0:
                self.err(t, "array length must be positive")
            return ArrT(self.resolve(t.elem), n)
        if isinstance(t, A.TNamed):
            if t.name in self.types:
                return self.types[t.name]
            self.err(t, "unknown type %%%s" % t.name)
        if isinstance(t, A.TFn):
            return FnT([self.resolve(p) for p in t.params],
                       self.resolve(t.ret))
        raise CheckError("internal: bad type node %r" % (t,))

    def member_types(self, d):
        """Type syntax nodes this declaration embeds."""
        if isinstance(d, A.StructDecl):
            return [t for (_, t) in d.fields]
        out = []
        for (_, ts) in d.variants:
            out.extend(ts)
        return out

    def type_ready_fn(self, t):
        return True

    def type_ready(self, t):
        if isinstance(t, A.TFn):
            return True
        """True when t's size is already known. Pointers never need the
        pointee to be complete, which is what makes recursive types legal."""
        if isinstance(t, A.TPtr):
            return True
        if isinstance(t, A.TArr):
            if isinstance(t.n, str) and t.n not in self.constants:
                return False
            return self.type_ready(t.elem)
        if isinstance(t, A.TNamed):
            nt = self.types.get(t.name)
            return nt is not None and nt.complete
        if isinstance(t, A.TName):
            if t.name in PRIMS:
                return True
            nt = self.types.get(t.name)
            return nt is not None and nt.complete
        return True

    def collect(self):
        # 1. create named type shells
        for fname, d in self.decls:
            self.file = fname
            if isinstance(d, A.StructDecl):
                if d.name in self.types and d.name != "Str":
                    self.err(d, "type %r declared twice" % d.name)
                self.types[d.name] = StructT(d.name)
            elif isinstance(d, A.SumDecl):
                if d.name in self.types:
                    self.err(d, "type %r declared twice" % d.name)
                self.types[d.name] = SumT(d.name)
        # 2. resolve $$ constants and lay out named types together, to a
        #    fixpoint: an array length may be a constant, and a constant may
        #    be #T of a type that is still being laid out.
        pending = [(fn, d) for (fn, d) in self.decls
                   if isinstance(d, (A.StructDecl, A.SumDecl))]
        pending_c = [(fn, d) for (fn, d) in self.decls
                     if isinstance(d, A.GlobalDecl) and d.const]
        while pending or pending_c:
            rest = []
            rest_c = []
            progress = False
            for fname, d in pending_c:
                self.file = fname
                if d.init is None:
                    self.err(d, "a $$ constant needs a value")
                cv = self.const_eval(d.init)
                if cv is None:
                    rest_c.append((fname, d))
                    continue
                if d.name in self.constants or d.name in self.globals:
                    self.err(d, "global %r declared twice" % d.name)
                ty = self.resolve(d.ty)
                if ty.kind not in ("int", "bool", "ptr"):
                    self.err(d, "a $$ constant must be a scalar")
                self.constants[d.name] = (ty, cv)
                progress = True
            pending_c = rest_c
            for fname, d in pending:
                self.file = fname
                if all(self.type_ready(t) for t in self.member_types(d)):
                    if isinstance(d, A.StructDecl):
                        fields = [(n, self.resolve(t)) for (n, t) in d.fields]
                        seen = set()
                        for (n, _) in fields:
                            if n in seen:
                                self.err(d, "duplicate field %r" % n)
                            seen.add(n)
                        self.types[d.name].layout(fields)
                    else:
                        vs = [(n, [self.resolve(t) for t in ts])
                              for (n, ts) in d.variants]
                        self.types[d.name].layout(vs)
                    progress = True
                else:
                    rest.append((fname, d))
            if not progress:
                if rest:
                    names = ", ".join("%" + d.name for _, d in rest)
                    self.file = rest[0][0]
                    self.err(rest[0][1],
                             "types contain each other by value: %s "
                             "(use a pointer to break the cycle)" % names)
                self.file = pending_c[0][0]
                self.err(pending_c[0][1],
                         "$$ constant %r cannot be computed at compile time"
                         % pending_c[0][1].name)
            pending = rest
        # 3. globals
        for fname, d in self.decls:
            self.file = fname
            if isinstance(d, A.GlobalDecl):
                ty = self.resolve(d.ty)
                if d.const:
                    continue        # already resolved in step 2
                if d.name in self.globals or d.name in self.constants:
                    self.err(d, "global %r declared twice" % d.name)
                label = "$g_" + d.name
                init = None
                if d.init is not None:
                    if ty.kind == "float":
                        fv = self.const_float(d.init)
                        if fv is None:
                            self.err(d, "a float global needs a literal value")
                        init = (struct.pack("<d", fv) if ty.bits == 64
                                else struct.pack("<f", fv))
                    else:
                        v = self.const_eval(d.init)
                        if v is None:
                            self.err(d, "global initialiser must be a constant")
                        if ty.kind not in ("int", "bool", "ptr"):
                            self.err(d, "only scalar globals may have an "
                                        "initialiser")
                        init = int(v).to_bytes(ty.size, "little",
                                               signed=(v < 0))
                self.globals[d.name] = (ty, label, d.mut)
                self.prog.globals[label] = (ty.size, ty.align, init)
        # 4. function signatures
        for fname, d in self.decls:
            self.file = fname
            if isinstance(d, A.FnDecl):
                if d.name in self.fns:
                    self.err(d, "function %r declared twice" % d.name)
                ps = [self.resolve(t) for (_, t) in d.params]
                rt = self.resolve(d.ret)
                if d.entry:
                    if ps:
                        self.err(d, "the entry function @! takes no parameters")
                    if rt != S64:
                        self.err(d, "the entry function @! must return s64")
                self.fns[d.name] = FnT(ps, rt)
        if "@!" not in self.fns:
            raise CheckError("no entry function: every program needs @! () s64")

    # -- constant folding ----------------------------------------------------
    def const_float(self, e):
        """A float literal, optionally negated."""
        if isinstance(e, A.FltLit):
            return e.v
        if isinstance(e, A.IntLit):
            return float(e.v)
        if isinstance(e, A.Un) and e.op == "-":
            inner = self.const_float(e.a)
            return None if inner is None else -inner
        return None

    def const_eval(self, e):
        if isinstance(e, A.IntLit):
            return e.v
        if isinstance(e, A.Ident):
            c = self.constants.get(e.name)
            return c[1] if c is not None else None
        if isinstance(e, A.SizeOf):
            if not self.type_ready(e.ty):
                return None
            return self.resolve(e.ty).size
        if isinstance(e, A.Un):
            a = self.const_eval(e.a)
            if a is None:
                return None
            if e.op == "-":
                return -a
            if e.op == "~":
                return ~a
            if e.op == "!":
                return 0 if a else 1
        if isinstance(e, A.Bin):
            a = self.const_eval(e.a)
            b = self.const_eval(e.b)
            if a is None or b is None:
                return None
            try:
                return {
                    "+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b,
                    "/": lambda: abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1),
                    "%": lambda: a - (abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1)) * b,
                    "&": lambda: a & b, "|": lambda: a | b, "^": lambda: a ^ b,
                    "<<": lambda: a << b, ">>": lambda: a >> b,
                    "==": lambda: int(a == b), "!=": lambda: int(a != b),
                    "<": lambda: int(a < b), ">": lambda: int(a > b),
                    "<=": lambda: int(a <= b), ">=": lambda: int(a >= b),
                }[e.op]()
            except (KeyError, ZeroDivisionError):
                return None
        return None

    # ====================================================================
    #                          function lowering
    # ====================================================================
    def lower_all(self):
        for fname, d in self.decls:
            self.file = fname
            if isinstance(d, A.FnDecl):
                self.lower_fn(d)
        return self.prog

    def addr_taken(self, body):
        """Names whose address is taken anywhere in this function."""
        out = set()

        def walk(n):
            if isinstance(n, list):
                for x in n:
                    walk(x)
                return
            if not isinstance(n, A.Node):
                return
            if isinstance(n, A.Addr) and isinstance(n.e, A.Ident):
                out.add(n.e.name)
            for f in getattr(n, "__slots__", ()):
                v = getattr(n, f, None)
                if isinstance(v, (list, tuple)):
                    for x in v:
                        if isinstance(x, (A.Node, list, tuple)):
                            walk(list(x) if isinstance(x, tuple) else x)
                elif isinstance(v, A.Node):
                    walk(v)
        walk(body)
        return out

    def lower_fn(self, d):
        sig = self.fns[d.name]
        sret = sig.ret.is_agg
        f = ir.Func(d.name, [], sig.ret, sret)
        self.f = f
        self.cur_ret = sig.ret
        self.scope = Scope()
        self.loops = []
        taken = self.addr_taken(d.body)

        if sret:
            v = f.vreg()
            f.params.append(("$sret", PtrT(sig.ret), v))
            self.cur_sret = v
        else:
            self.cur_sret = None

        for (pname, pty_ast), pty in zip(d.params, sig.params):
            if pty.is_agg:
                # arrives as a pointer to the caller's copy; copy it locally
                pv = f.vreg()
                f.params.append((pname, PtrT(pty), pv))
                s = f.slot(pty.size, pty.align, pname)
                dst = f.vreg()
                f.emit("lea", dst, s)
                f.emit("memcpy", dst, pv, pty.size)
                self.scope.put(pname, ("slot", s, pty, False))
            else:
                pv = f.vreg(pty.kind == "float")
                f.params.append((pname, pty, pv))
                if pname in taken:
                    s = f.slot(pty.size, pty.align, pname)
                    av = f.vreg()
                    f.emit("lea", av, s)
                    f.emit("store", av, pv, pty.size, pty.kind == "float")
                    self.scope.put(pname, ("slot", s, pty, True))
                else:
                    self.scope.put(pname, ("vreg", pv, pty, True))

        self.taken = taken
        for st in d.body:
            self.stmt(st)

        # implicit return for void functions
        if sig.ret == VOID:
            f.emit("ret", None, False)
        else:
            f.emit("trap")
        self.prog.funcs.append(f)
        if d.entry:
            self.prog.entry = f
        self.f = None

    # -- statements ----------------------------------------------------------
    def block(self, stmts):
        saved = self.scope
        self.scope = Scope(saved)
        for s in stmts:
            self.stmt(s)
        self.scope = saved

    def stmt(self, s):
        f = self.f
        if isinstance(s, A.Let):
            ty = self.resolve(s.ty) if s.ty is not None else None
            if s.init is None:
                # `$~ name T` with no value is zero-initialised
                if ty.is_agg:
                    slot = f.slot(ty.size, ty.align, s.name)
                    av = f.vreg()
                    f.emit("lea", av, slot)
                    f.emit("memzero", av, ty.size)
                    self.scope.put(s.name, ("slot", slot, ty, s.mut))
                    return
                z = f.vreg(ty.kind == "float")
                if ty.kind == "float":
                    f.emit("fconst", z, 0.0, ty.bits)
                else:
                    f.emit("const", z, 0)
                if s.name in self.taken:
                    slot = f.slot(ty.size, ty.align, s.name)
                    av = f.vreg()
                    f.emit("lea", av, slot)
                    f.emit("store", av, z, ty.size, ty.kind == "float")
                    self.scope.put(s.name, ("slot", slot, ty, s.mut))
                else:
                    self.scope.put(s.name, ("vreg", z, ty, s.mut))
                return
            v, vt = self.rval(s.init, ty)
            if ty is None:
                ty = vt
            else:
                self.assignable(s, ty, vt)
            if ty == VOID:
                self.err(s, "cannot bind a value of type v")
            if self.scope.names.get(s.name) is not None:
                self.err(s, "%r is already bound in this block" % s.name)
            if ty.is_agg:
                slot = f.slot(ty.size, ty.align, s.name)
                dst = f.vreg()
                f.emit("lea", dst, slot)
                f.emit("memcpy", dst, v, ty.size)
                self.scope.put(s.name, ("slot", slot, ty, s.mut))
            elif s.name in self.taken:
                slot = f.slot(ty.size, ty.align, s.name)
                av = f.vreg()
                f.emit("lea", av, slot)
                f.emit("store", av, v, ty.size, ty.kind == "float")
                self.scope.put(s.name, ("slot", slot, ty, s.mut))
            else:
                nv = f.vreg(ty.kind == "float")
                f.emit("mov", nv, v)
                self.scope.put(s.name, ("vreg", nv, ty, s.mut))
            return

        if isinstance(s, A.Assign):
            if isinstance(s.target, A.Ident):
                ent = self.scope.get(s.target.name)
                if ent and not ent[3]:
                    self.err(s, "%r is immutable; declare it with $~ to assign"
                             % s.target.name)
                if ent and ent[0] == "vreg":
                    v, vt = self.rval(s.value, ent[2])
                    self.assignable(s, ent[2], vt)
                    f.emit("mov", ent[1], v)
                    return
                if ent is None:
                    if s.target.name in self.constants:
                        self.err(s, "%r is a $$ constant and cannot be "
                                    "assigned" % s.target.name)
                    g = self.globals.get(s.target.name)
                    if g is not None and not g[2]:
                        self.err(s, "%r is immutable; declare it with $~ to "
                                    "assign" % s.target.name)
            addr, ty = self.lval(s.target)
            v, vt = self.rval(s.value, ty)
            self.assignable(s, ty, vt)
            if ty.is_agg:
                f.emit("memcpy", addr, v, ty.size)
            else:
                f.emit("store", addr, v, ty.size, ty.kind == "float")
            return

        if isinstance(s, A.Return):
            if s.value is None:
                if self.cur_ret != VOID:
                    self.err(s, "this function must return %s" % self.cur_ret)
                f.emit("ret", None, False)
                return
            v, vt = self.rval(s.value, self.cur_ret)
            self.assignable(s, self.cur_ret, vt)
            if self.cur_ret.is_agg:
                f.emit("memcpy", self.cur_sret, v, self.cur_ret.size)
                f.emit("ret", self.cur_sret, False)
            else:
                f.emit("ret", v, self.cur_ret.kind == "float")
            return

        if isinstance(s, A.If):
            c, ct = self.rval(s.cond, BOOL)
            if ct != BOOL:
                self.err(s, "condition must be b, got %s" % ct)
            lt = f.label("then")
            le = f.label("else")
            lx = f.label("endif")
            f.emit("br", c, lt, le if s.els else lx)
            f.emit("label", lt)
            self.block(s.then)
            f.emit("jmp", lx)
            if s.els:
                f.emit("label", le)
                self.block(s.els)
                f.emit("jmp", lx)
            f.emit("label", lx)
            return

        if isinstance(s, A.While):
            lc = f.label("cond")
            lb = f.label("body")
            lx = f.label("endloop")
            f.emit("jmp", lc)
            f.emit("label", lc)
            c, ct = self.rval(s.cond, BOOL)
            if ct != BOOL:
                self.err(s, "loop condition must be b, got %s" % ct)
            f.emit("br", c, lb, lx)
            f.emit("label", lb)
            self.loops.append((lc, lx))
            self.block(s.body)
            self.loops.pop()
            f.emit("jmp", lc)
            f.emit("label", lx)
            return

        if isinstance(s, A.Break):
            if not self.loops:
                self.err(s, "*< outside a loop")
            f.emit("jmp", self.loops[-1][1])
            return

        if isinstance(s, A.Continue):
            if not self.loops:
                self.err(s, "*> outside a loop")
            f.emit("jmp", self.loops[-1][0])
            return

        if isinstance(s, A.Match):
            self.lower_match(s)
            return

        if isinstance(s, A.ExprStmt):
            self.rval(s.expr, None)
            return

        if isinstance(s, A.AsmBytes):
            f.emit("rawbytes", bytes(s.values))
            return

        raise CheckError("internal: unhandled statement %r" % (s,))

    def lower_match(self, s):
        f = self.f
        addr, ty = self.rval(s.subject, None)
        if ty.kind != "sum":
            self.err(s, "?? needs a sum type, got %s" % ty)
        tag = f.vreg()
        f.emit("load", tag, addr, 8, True, False)
        lx = f.label("endmatch")
        covered = set()
        has_wild = False
        arm_labels = []
        for (pat, body) in s.arms:
            arm_labels.append(f.label("arm"))
        for k, (pat, body) in enumerate(s.arms):
            if isinstance(pat, A.PWild):
                has_wild = True
                if k != len(s.arms) - 1:
                    self.err(pat, "|_ must be the final arm")
                f.emit("jmp", arm_labels[k])
                break
            idx, v = ty.variant(pat.variant)
            if idx is None:
                self.err(pat, "%s has no variant %r" % (ty, pat.variant))
            if pat.variant in covered:
                self.err(pat, "variant %r matched twice" % pat.variant)
            covered.add(pat.variant)
            if len(pat.binds) != len(v[1]):
                self.err(pat, "variant %r binds %d value(s), got %d"
                         % (pat.variant, len(v[1]), len(pat.binds)))
            c = f.vreg()
            k2 = f.vreg()
            f.emit("const", k2, idx)
            f.emit("cmp", c, "==", tag, k2, True)
            nxt = f.label("next")
            f.emit("br", c, arm_labels[k], nxt)
            f.emit("label", nxt)
        if not has_wild and len(covered) != len(ty.variants):
            missing = [v[0] for v in ty.variants if v[0] not in covered]
            self.err(s, "?? is not exhaustive; missing %s (add |_ to ignore)"
                     % ", ".join(missing))
        if not has_wild:
            f.emit("jmp", lx)
        for k, (pat, body) in enumerate(s.arms):
            f.emit("label", arm_labels[k])
            saved = self.scope
            self.scope = Scope(saved)
            if isinstance(pat, A.PVar):
                idx, v = ty.variant(pat.variant)
                for bname, bty, boff in zip(pat.binds, v[1], v[2]):
                    off = f.vreg()
                    f.emit("const", off, boff)
                    pa = f.vreg()
                    f.emit("bin", pa, "+", addr, off, U64)
                    if bty.is_agg:
                        self.scope.put(bname, ("addr", pa, bty, False))
                    else:
                        bv = f.vreg(bty.kind == "float")
                        f.emit("load", bv, pa, bty.size, bty.kind == "int" and bty.signed,
                               bty.kind == "float")
                        self.scope.put(bname, ("vreg", bv, bty, False))
            for st in body:
                self.stmt(st)
            self.scope = saved
            f.emit("jmp", lx)
        f.emit("label", lx)

    # -- assignability -------------------------------------------------------
    def assignable(self, node, want, got):
        if want == got:
            return
        # array -> pointer decay
        if want.kind == "ptr" and got.kind == "arr" and want.to == got.elem:
            return
        if want.kind == "ptr" and got.kind == "ptr" and str(got.to) == "v":
            return
        if want.kind == "ptr" and got.kind == "ptr" and str(want.to) == "v":
            return
        self.err(node, "type mismatch: expected %s, got %s" % (want, got))

    # -- lvalues -------------------------------------------------------------
    def lval(self, e):
        f = self.f
        if isinstance(e, A.Ident):
            ent = self.scope.get(e.name)
            if ent is None:
                if e.name in self.constants:
                    self.err(e, "%r is a $$ constant and has no address"
                             % e.name)
                if e.name in self.globals:
                    ty, label, mut = self.globals[e.name]
                    v = f.vreg()
                    f.emit("leag", v, label)
                    return v, ty
                self.err(e, "unknown name %r" % e.name)
            kind, val, ty, mut = ent
            if kind == "slot":
                v = f.vreg()
                f.emit("lea", v, val)
                return v, ty
            if kind == "addr":
                return val, ty
            self.err(e, "%r has no address here" % e.name)
        if isinstance(e, A.Deref):
            v, ty = self.rval(e.p, None)
            if ty.kind != "ptr":
                self.err(e, "cannot dereference %s" % ty)
            return v, ty.to
        if isinstance(e, A.Field):
            base, bty = self.field_base(e)
            if bty.kind != "struct":
                self.err(e, "%s has no fields" % bty)
            fld = bty.field(e.name)
            if fld is None:
                self.err(e, "%s has no field %r" % (bty, e.name))
            off = f.vreg()
            f.emit("const", off, fld[2])
            r = f.vreg()
            f.emit("bin", r, "+", base, off, U64)
            return r, fld[1]
        if isinstance(e, A.Index):
            base, bty = self.rval(e.base, None)
            if bty.kind == "arr":
                elem = bty.elem
            elif bty.kind == "ptr":
                elem = bty.to
            else:
                self.err(e, "cannot index %s" % bty)
            iv, ity = self.rval(e.idx, S64)
            if ity.kind != "int":
                self.err(e, "index must be an integer, got %s" % ity)
            sz = f.vreg()
            f.emit("const", sz, elem.size)
            off = f.vreg()
            f.emit("bin", off, "*", iv, sz, U64)
            r = f.vreg()
            f.emit("bin", r, "+", base, off, U64)
            return r, elem
        self.err(e, "not assignable")

    def field_base(self, e):
        """Address of the struct a field access applies to (auto-derefs *%S)."""
        f = self.f
        b = e.base
        v, ty = self.rval(b, None)
        if ty.kind == "ptr" and ty.to.kind == "struct":
            return v, ty.to
        if ty.kind == "struct":
            return v, ty
        self.err(e, "%s has no fields" % ty)

    # -- rvalues -------------------------------------------------------------
    def rval(self, e, want):
        f = self.f

        if isinstance(e, A.IntLit):
            ty = want if (want is not None and want.kind in ("int", "ptr", "bool")) else S64
            if ty.kind == "bool" and e.v not in (0, 1):
                ty = S64
            v = f.vreg()
            f.emit("const", v, e.v & 0xFFFFFFFFFFFFFFFF if e.v >= 0 else e.v)
            return v, ty

        if isinstance(e, A.FltLit):
            ty = want if (want is not None and want.kind == "float") else F64
            v = f.vreg(True)
            f.emit("fconst", v, e.v, ty.bits)
            return v, ty

        if isinstance(e, A.StrLit):
            lbl = self.prog.add_ro(e.v + b"\0")
            s = f.slot(self.str_t.size, self.str_t.align, "str")
            base = f.vreg()
            f.emit("lea", base, s)
            p = f.vreg()
            f.emit("leas", p, lbl)
            f.emit("store", base, p, 8, False)
            off = f.vreg()
            f.emit("const", off, 8)
            a2 = f.vreg()
            f.emit("bin", a2, "+", base, off, U64)
            n = f.vreg()
            f.emit("const", n, len(e.v))
            f.emit("store", a2, n, 8, False)
            return base, self.str_t

        if isinstance(e, A.SizeOf):
            v = f.vreg()
            f.emit("const", v, self.resolve(e.ty).size)
            return v, S64

        if isinstance(e, A.Ident):
            ent = self.scope.get(e.name)
            if ent is None:
                if e.name in self.constants:
                    cty, cv = self.constants[e.name]
                    cvr = f.vreg()
                    f.emit("const", cvr, cv & 0xFFFFFFFFFFFFFFFF)
                    return cvr, cty
                if e.name in self.globals:
                    ty, label, _ = self.globals[e.name]
                    a = f.vreg()
                    f.emit("leag", a, label)
                    if ty.is_agg:
                        return a, ty
                    v = f.vreg(ty.kind == "float")
                    f.emit("load", v, a, ty.size,
                           ty.kind == "int" and ty.signed, ty.kind == "float")
                    return v, ty
                self.err(e, "unknown name %r" % e.name)
            kind, val, ty, mut = ent
            if kind == "vreg":
                return val, ty
            if kind == "addr":
                if ty.is_agg:
                    return val, ty
                v = f.vreg(ty.kind == "float")
                f.emit("load", v, val, ty.size,
                       ty.kind == "int" and ty.signed, ty.kind == "float")
                return v, ty
            a = f.vreg()
            f.emit("lea", a, val)
            if ty.is_agg:
                return a, ty
            v = f.vreg(ty.kind == "float")
            f.emit("load", v, a, ty.size,
                   ty.kind == "int" and ty.signed, ty.kind == "float")
            return v, ty

        if isinstance(e, A.Addr):
            a, ty = self.lval(e.e)
            return a, PtrT(ty)

        if isinstance(e, A.Deref):
            a, ty = self.lval(e)
            if ty.is_agg:
                return a, ty
            v = f.vreg(ty.kind == "float")
            f.emit("load", v, a, ty.size,
                   ty.kind == "int" and ty.signed, ty.kind == "float")
            return v, ty

        if isinstance(e, (A.Field, A.Index)):
            a, ty = self.lval(e)
            if ty.is_agg:
                return a, ty
            v = f.vreg(ty.kind == "float")
            f.emit("load", v, a, ty.size,
                   ty.kind == "int" and ty.signed, ty.kind == "float")
            return v, ty

        if isinstance(e, A.Cast):
            return self.lower_cast(e, want)

        if isinstance(e, A.Un):
            return self.lower_un(e, want)

        if isinstance(e, A.Bin):
            return self.lower_bin(e, want)

        if isinstance(e, A.Call):
            return self.lower_call(e)

        if isinstance(e, A.CallP):
            fv, ft = self.rval(e.callee, None)
            if ft.kind != "fn":
                self.err(e, "cannot call a value of type %s" % ft)
            return self.lower_indirect(e, fv, ft, e.args)

        if isinstance(e, A.FnRef):
            sig = self.fns.get(e.name)
            if sig is None:
                self.err(e, "unknown function %r" % e.name)
            v = f.vreg()
            f.emit("leaf", v, e.name)
            return v, sig

        if isinstance(e, A.Syscall):
            args = []
            if len(e.args) > 6:
                self.err(e, "a syscall takes at most 6 arguments")
            for a in e.args:
                av, at = self.rval(a, S64)
                if at.kind not in ("int", "ptr", "bool"):
                    if at.kind == "arr":
                        pass
                    else:
                        self.err(e, "syscall arguments must be scalar, got %s" % at)
                args.append(av)
            d = f.vreg()
            f.emit("syscall", d, e.num, args)
            f.calls = True
            return d, S64

        if isinstance(e, A.StructLit):
            ty = self.types.get(e.tyname)
            if ty is None or ty.kind != "struct":
                self.err(e, "unknown struct %%%s" % e.tyname)
            given = {}
            for (fn, fe) in e.inits:
                if fn in given:
                    self.err(e, "field %r initialised twice" % fn)
                given[fn] = fe
            missing = [x[0] for x in ty.fields if x[0] not in given]
            if missing:
                self.err(e, "struct literal missing field(s): %s" % ", ".join(missing))
            extra = [k for k in given if ty.field(k) is None]
            if extra:
                self.err(e, "%s has no field %r" % (ty, extra[0]))
            s = f.slot(ty.size, ty.align, e.tyname)
            base = f.vreg()
            f.emit("lea", base, s)
            for (fn, fty, foff) in ty.fields:
                v, vt = self.rval(given[fn], fty)
                self.assignable(e, fty, vt)
                off = f.vreg()
                f.emit("const", off, foff)
                a = f.vreg()
                f.emit("bin", a, "+", base, off, U64)
                if fty.is_agg:
                    f.emit("memcpy", a, v, fty.size)
                else:
                    f.emit("store", a, v, fty.size, fty.kind == "float")
            return base, ty

        if isinstance(e, A.SumLit):
            ty = self.types.get(e.tyname)
            if ty is None or ty.kind != "sum":
                self.err(e, "unknown sum type %%%s" % e.tyname)
            idx, v = ty.variant(e.variant)
            if idx is None:
                self.err(e, "%s has no variant %r" % (ty, e.variant))
            if len(e.args) != len(v[1]):
                self.err(e, "variant %r takes %d value(s), got %d"
                         % (e.variant, len(v[1]), len(e.args)))
            s = f.slot(ty.size, ty.align, e.tyname)
            base = f.vreg()
            f.emit("lea", base, s)
            t = f.vreg()
            f.emit("const", t, idx)
            f.emit("store", base, t, 8, False)
            for arg, aty, aoff in zip(e.args, v[1], v[2]):
                av, avt = self.rval(arg, aty)
                self.assignable(e, aty, avt)
                off = f.vreg()
                f.emit("const", off, aoff)
                a = f.vreg()
                f.emit("bin", a, "+", base, off, U64)
                if aty.is_agg:
                    f.emit("memcpy", a, av, aty.size)
                else:
                    f.emit("store", a, av, aty.size, aty.kind == "float")
            return base, ty

        if isinstance(e, A.ArrLit):
            if not e.items:
                self.err(e, "empty array literal needs a declared type")
            elem = want.elem if (want is not None and want.kind == "arr") else None
            vals = []
            for it in e.items:
                v, vt = self.rval(it, elem)
                if elem is None:
                    elem = vt
                else:
                    self.assignable(e, elem, vt)
                vals.append(v)
            ty = ArrT(elem, len(vals))
            s = f.slot(ty.size, ty.align, "arr")
            base = f.vreg()
            f.emit("lea", base, s)
            for k, v in enumerate(vals):
                off = f.vreg()
                f.emit("const", off, k * elem.size)
                a = f.vreg()
                f.emit("bin", a, "+", base, off, U64)
                if elem.is_agg:
                    f.emit("memcpy", a, v, elem.size)
                else:
                    f.emit("store", a, v, elem.size, elem.kind == "float")
            return base, ty

        raise CheckError("internal: unhandled expression %r" % (e,))

    # -- casts ---------------------------------------------------------------
    def lower_cast(self, e, want):
        f = self.f
        to = self.resolve(e.ty)
        v, vt = self.rval(e.e, None)
        if vt.is_agg or to.is_agg:
            self.err(e, "cannot cast aggregates")
        if to == vt:
            return v, to
        d = f.vreg(to.kind == "float")
        f.emit("cvt", d, v, vt, to)
        return d, to

    # -- unary ---------------------------------------------------------------
    def lower_un(self, e, want):
        f = self.f
        if e.op == "!":
            v, ty = self.rval(e.a, BOOL)
            if ty != BOOL:
                self.err(e, "! needs b, got %s" % ty)
            z = f.vreg()
            f.emit("const", z, 0)
            d = f.vreg()
            f.emit("cmp", d, "==", v, z, False)
            return d, BOOL
        v, ty = self.rval(e.a, want)
        if e.op == "-":
            if ty.kind == "float":
                d = f.vreg(True)
                f.emit("fun", d, "-", v, ty.bits)
                return d, ty
            if ty.kind != "int":
                self.err(e, "- needs a number, got %s" % ty)
            d = f.vreg()
            f.emit("un", d, "-", v, ty)
            return d, ty
        if e.op == "~":
            if ty.kind != "int":
                self.err(e, "~ needs an integer, got %s" % ty)
            d = f.vreg()
            f.emit("un", d, "~", v, ty)
            return d, ty
        raise CheckError("internal: unary %r" % e.op)

    # -- binary --------------------------------------------------------------
    def lower_bin(self, e, want):
        f = self.f
        op = e.op

        if op in ("&&", "||"):
            a, at = self.rval(e.a, BOOL)
            if at != BOOL:
                self.err(e, "%s needs b, got %s" % (op, at))
            d = f.vreg()
            lrhs = f.label("sc")
            lend = f.label("scend")
            f.emit("mov", d, a)
            if op == "&&":
                f.emit("br", a, lrhs, lend)
            else:
                f.emit("br", a, lend, lrhs)
            f.emit("label", lrhs)
            b, bt = self.rval(e.b, BOOL)
            if bt != BOOL:
                self.err(e, "%s needs b, got %s" % (op, bt))
            f.emit("mov", d, b)
            f.emit("jmp", lend)
            f.emit("label", lend)
            return d, BOOL

        a, at = self.rval(e.a, want if op not in CMP else None)
        b, bt = self.rval(e.b, at)

        if op in CMP:
            if at.kind == "float" or bt.kind == "float":
                if at != bt:
                    self.err(e, "cannot compare %s with %s" % (at, bt))
                d = f.vreg()
                f.emit("fcmp", d, op, a, b, at.bits)
                return d, BOOL
            ok = (at == bt) or (at.kind == "ptr" and bt.kind == "ptr")
            if not ok:
                self.err(e, "cannot compare %s with %s" % (at, bt))
            signed = (at.kind == "int" and at.signed)
            d = f.vreg()
            f.emit("cmp", d, op, a, b, signed)
            return d, BOOL

        # pointer arithmetic: *T + int  /  *T - int
        if at.kind == "ptr" and bt.kind == "int" and op in ("+", "-"):
            sz = f.vreg()
            f.emit("const", sz, at.to.size)
            scaled = f.vreg()
            f.emit("bin", scaled, "*", b, sz, U64)
            d = f.vreg()
            f.emit("bin", d, op, a, scaled, U64)
            return d, at
        if at.kind == "ptr" and bt.kind == "ptr" and op == "-":
            diff = f.vreg()
            f.emit("bin", diff, "-", a, b, U64)
            sz = f.vreg()
            f.emit("const", sz, at.to.size)
            d = f.vreg()
            f.emit("bin", d, "/", diff, sz, S64)
            return d, S64

        if at.kind == "float":
            if at != bt:
                self.err(e, "type mismatch: %s %s %s" % (at, op, bt))
            if op not in FLT_BIN:
                self.err(e, "operator %r is not defined on %s" % (op, at))
            d = f.vreg(True)
            f.emit("fbin", d, op, a, b, at.bits)
            return d, at

        if at.kind != "int" or bt.kind != "int":
            self.err(e, "operator %r needs numbers, got %s and %s" % (op, at, bt))
        if at != bt:
            self.err(e, "type mismatch: %s %s %s (VIBE never converts silently)"
                     % (at, op, bt))
        if op not in INT_BIN:
            self.err(e, "operator %r is not defined on %s" % (op, at))
        d = f.vreg()
        f.emit("bin", d, op, a, b, at)
        return d, at

    # -- calls ---------------------------------------------------------------
    def lower_call(self, e):
        f = self.f
        sig = self.fns.get(e.name)
        if sig is None:
            # a local or global holding a function pointer is callable too
            ent = self.scope.get(e.name)
            known = (ent is not None or e.name in self.globals)
            if known:
                fv, ft = self.rval(A.Ident(e.name, line=e.line, col=e.col), None)
                if ft.kind != "fn":
                    self.err(e, "%r is not callable (it is %s)" % (e.name, ft))
                return self.lower_indirect(e, fv, ft, e.args)
            self.err(e, "unknown function %r" % e.name)
        if len(e.args) != len(sig.params):
            self.err(e, "%s takes %d argument(s), got %d"
                     % (e.name, len(sig.params), len(e.args)))
        f.calls = True
        argv = []
        argf = []
        retslot = None
        if sig.ret.is_agg:
            retslot = f.slot(sig.ret.size, sig.ret.align, "ret")
            rv = f.vreg()
            f.emit("lea", rv, retslot)
            argv.append(rv)
            argf.append(False)
        for a, pt in zip(e.args, sig.params):
            v, vt = self.rval(a, pt)
            self.assignable(e, pt, vt)
            if pt.is_agg:
                # pass a private copy by reference
                s = f.slot(pt.size, pt.align, "argcopy")
                c = f.vreg()
                f.emit("lea", c, s)
                f.emit("memcpy", c, v, pt.size)
                argv.append(c)
                argf.append(False)
            else:
                argv.append(v)
                argf.append(pt.kind == "float")
        if len(argv) > 6:
            self.err(e, "at most 6 arguments are supported in this release")
        if sig.ret == VOID:
            f.emit("call", None, e.name, argv, argf, False)
            return None, VOID
        d = f.vreg(sig.ret.kind == "float")
        f.emit("call", d, e.name, argv, argf, sig.ret.kind == "float")
        if sig.ret.is_agg:
            return d, sig.ret
        return d, sig.ret


    def lower_indirect(self, e, fv, sig, argexprs):
        """Call through a function pointer. Same ABI as a direct call."""
        f = self.f
        if len(argexprs) != len(sig.params):
            self.err(e, "this function takes %d argument(s), got %d"
                     % (len(sig.params), len(argexprs)))
        f.calls = True
        argv = []
        argf = []
        if sig.ret.is_agg:
            rs = f.slot(sig.ret.size, sig.ret.align, "ret")
            rv = f.vreg()
            f.emit("lea", rv, rs)
            argv.append(rv)
            argf.append(False)
        for a, pt in zip(argexprs, sig.params):
            v, vt = self.rval(a, pt)
            self.assignable(e, pt, vt)
            if pt.is_agg:
                sl = f.slot(pt.size, pt.align, "argcopy")
                c = f.vreg()
                f.emit("lea", c, sl)
                f.emit("memcpy", c, v, pt.size)
                argv.append(c)
                argf.append(False)
            else:
                argv.append(v)
                argf.append(pt.kind == "float")
        if len(argv) > 6:
            self.err(e, "at most 6 arguments are supported in this release")
        if sig.ret == VOID:
            f.emit("calli", None, fv, argv, argf, False)
            return None, VOID
        d = f.vreg(sig.ret.kind == "float")
        f.emit("calli", d, fv, argv, argf, sig.ret.kind == "float")
        return d, sig.ret


def build(path, include_dirs=()):
    fe = Front(include_dirs)
    fe.load(path)
    fe.collect()
    return fe.lower_all()
