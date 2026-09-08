"""VIBE code generator: IR -> x86-64 machine code -> ELF64 executable.

Every virtual register has a home slot in the frame. The allocator promotes
the hot ones into physical registers; anything it leaves in memory is
materialised through the scratch registers r10/r11 (xmm0-xmm2 for floats).
With `-O0` the allocator is skipped entirely and every value lives in memory,
which gives the test suite a second, independent execution path to compare
against.
"""

import struct

from . import elf
from .opt import optimise, prune, single_def_consts, defs_of, uses_of
from .regalloc import allocate, all_memory
from .x64 import (Asm, Mem, rip, RAX, RCX, RDX, RBX, RSP, RBP, RSI, RDI,
                  R8, R9, R10, R11, R12, R13, R14, R15,
                  SIGNED_CC, UNSIGNED_CC, INVERT_CC)

INT_ARG_REGS = [RDI, RSI, RDX, RCX, R8, R9]
SYS_ARG_REGS = [RDI, RSI, RDX, R10, R8, R9]
XT0, XT1, XT2 = 0, 1, 2          # xmm scratch


def is_pow2(k):
    return k > 0 and (k & (k - 1)) == 0


def log2(k):
    n = 0
    while k > 1:
        k >>= 1
        n += 1
    return n


class CodeGen:
    def __init__(self, prog, opt=True):
        self.prog = prog
        self.asm = Asm()
        self.opt = opt
        self.data = bytearray()
        self.data_syms = {}
        self.ro = bytearray()
        self.ro_syms = {}
        self.f = None
        self.loc = {}
        self.callee = []
        self.save_off = {}
        self.home = {}
        self.frameless = False
        self.pad = 0
        self.next_label = None

    # ---------------------------------------------------------------- data
    def build_data(self):
        for lbl, blob in self.prog.rodata:
            while len(self.ro) % 8:
                self.ro.append(0)
            self.ro_syms[lbl] = len(self.ro)
            self.ro += blob
        for lbl, (size, align, init) in self.prog.globals.items():
            a = max(align, 1)
            while len(self.data) % a:
                self.data.append(0)
            self.data_syms[lbl] = len(self.data)
            if init is not None:
                self.data += init
                self.data += b"\0" * (size - len(init))
            else:
                self.data += b"\0" * size

    # --------------------------------------------------------------- frame
    def layout_frame(self, f):
        """Only values the allocator left in memory get a home slot, so a
        function whose values all fit in registers needs no frame at all."""
        cur = 0
        self.home = {}
        live = set()
        for ins in f.ins:
            for x in defs_of(ins):
                live.add(x)
            for x in uses_of(ins):
                live.add(x)
        for (_, _, pv) in f.params:
            live.add(pv)
        for v in sorted(live):
            if self.loc.get(v, ("m",))[0] == "m":
                cur += 8
                self.home[v] = -cur
        stack_needed = (cur > 0)
        self.save_off = {}
        for r in self.callee:
            cur += 8
            self.save_off[r] = -cur
        for s in f.slots:
            a = max(s.align, 1)
            cur = (cur + a - 1) & ~(a - 1)
            cur += s.size
            s.off = -cur
        f.frame = (cur + 15) & ~15
        # a frame is only needed when something actually lives on the stack;
        # saved registers can go on the machine stack instead
        self.frameless = not stack_needed and not f.slots
        if self.frameless:
            f.frame = 0
        return f.frame

    def va(self, v):
        return Mem(RBP, self.home[v])

    # ------------------------------------------------------- value access
    def rd(self, v, scratch):
        """Physical register holding v (loading it if it lives in memory)."""
        l = self.loc[v]
        if l[0] == "r":
            return l[1]
        self.asm.mov_rm(scratch, self.va(v))
        return scratch

    def wreg(self, v, scratch):
        """Register to compute v into."""
        l = self.loc[v]
        return l[1] if l[0] == "r" else scratch

    def done(self, v, r):
        """Commit a value computed in `r` as the value of v."""
        l = self.loc[v]
        if l[0] == "r":
            if l[1] != r:
                self.asm.mov_rr(l[1], r)
        else:
            self.asm.mov_mr(self.va(v), r)

    def rdf(self, v, scratch):
        l = self.loc[v]
        if l[0] == "x":
            return l[1]
        self.asm.movsd_load(scratch, self.va(v), 64)
        return scratch

    def wregf(self, v, scratch):
        l = self.loc[v]
        return l[1] if l[0] == "x" else scratch

    def donef(self, v, x):
        l = self.loc[v]
        if l[0] == "x":
            if l[1] != x:
                self.asm.movsd_load(l[1], x, 64)
        else:
            self.asm.movsd_store(self.va(v), x, 64)

    def narrow(self, r, ty):
        if ty is None:
            return
        if ty.kind == "bool":
            self.asm.movzx(r, r, 1)
            return
        if ty.kind != "int" or ty.size == 8:
            return
        if ty.signed:
            self.asm.movsx(r, r, ty.size)
        else:
            self.asm.movzx(r, r, ty.size)

    # ------------------------------------------------------ parallel moves
    def parallel_move(self, moves, float_regs=False):
        """moves: list of (dst_phys, kind, val) with kind in 'r' | 'm' | 'i'.
        Performs them as if simultaneous."""
        pending = [list(m) for m in moves if not (m[1] == "r" and m[0] == m[2])]
        mv = (self.asm.movsd_load if float_regs else self.asm.mov_rr)
        while pending:
            srcs = {m[2] for m in pending if m[1] == "r"}
            for i, (d, k, val) in enumerate(pending):
                if d not in srcs:
                    self._emit_move(d, k, val, float_regs)
                    pending.pop(i)
                    break
            else:
                # every destination is also a source: break the cycle
                d0, k0, v0 = pending[0]
                if float_regs:
                    self.asm.movsd_load(XT2, v0, 64)
                    tmp = XT2
                else:
                    self.asm.mov_rr(R11, v0)
                    tmp = R11
                for m in pending:
                    if m[1] == "r" and m[2] == v0:
                        m[2] = tmp
        return

    def _emit_move(self, d, k, val, float_regs):
        a = self.asm
        if float_regs:
            if k == "r":
                a.movsd_load(d, val, 64)
            else:
                a.movsd_load(d, self.va(val), 64)
            return
        if k == "r":
            a.mov_rr(d, val)
        elif k == "m":
            a.mov_rm(d, self.va(val))
        else:
            a.mov_ri(d, val)

    def src_of(self, v):
        l = self.loc[v]
        return ("r", l[1]) if l[0] in ("r", "x") else ("m", v)

    # ------------------------------------------------------------- program
    def run(self):
        prune(self.prog)
        if self.opt:
            optimise(self.prog)
        a = self.asm
        # the kernel enters here with rsp pointing at argc; record it before
        # anything touches the stack
        a.mov_mr(rip("$g___sp"), RSP)
        a.call("@!")
        a.mov_rr(RDI, RAX)
        a.mov_ri(RAX, 60)
        a.syscall()
        a.ud2()

        for f in self.prog.funcs:
            self.gen_func(f)

        self.build_data()
        return self.link()

    def link(self):
        a = self.asm
        code = bytearray(a.buf)
        lay = elf.plan_layout(len(code), len(self.ro))
        for off, size, kind, target, addend in a.fixups:
            if kind == "rel":
                if target not in a.labels:
                    raise Exception("unresolved label %r" % target)
                val = a.labels[target] - (off + 4)
            elif kind == "rip":
                if target in self.ro_syms:
                    sym = lay["ro_vaddr"] + self.ro_syms[target]
                elif target in self.data_syms:
                    sym = lay["data_vaddr"] + self.data_syms[target]
                elif target in a.labels:
                    sym = lay["code_vaddr"] + a.labels[target]
                else:
                    raise Exception("unresolved symbol %r" % target)
                val = sym - (lay["code_vaddr"] + off + 4)
            else:
                raise Exception("bad fixup kind " + kind)
            code[off:off + 4] = struct.pack("<i", val)
        return elf.build_elf(bytes(code), bytes(self.ro), bytes(self.data), 0)

    # ------------------------------------------------------- one function
    def gen_func(self, f):
        a = self.asm
        self.f = f
        if self.opt:
            self.loc, self.callee = allocate(f)
        else:
            self.loc, self.callee = all_memory(f)
        frame = self.layout_frame(f)

        a.label(f.name)
        if self.frameless:
            for r in self.callee:
                a.push(r)
            # keep rsp 16-byte aligned at any call we make
            self.pad = 8 if (len(self.callee) % 2 == 0) else 0
            if self.pad and f.calls:
                a.alu_ri("-", RSP, self.pad)
            else:
                self.pad = 0
        else:
            self.pad = 0
            a.push(RBP)
            a.mov_rr(RBP, RSP)
            if frame:
                a.alu_ri("-", RSP, frame)
            for r in self.callee:
                a.mov_mr(Mem(RBP, self.save_off[r]), r)

        # incoming arguments: memory homes first (they only read the ABI
        # registers), then a simultaneous move into allocated registers
        ints = 0
        flts = 0
        gp_moves = []
        xmm_moves = []
        for (pname, pty, pv) in f.params:
            if pty.kind == "float":
                src = flts
                flts += 1
                if self.loc[pv][0] == "x":
                    xmm_moves.append((self.loc[pv][1], "r", src))
                else:
                    a.movsd_store(self.va(pv), src, 64)
            else:
                src = INT_ARG_REGS[ints]
                ints += 1
                if self.loc[pv][0] == "r":
                    gp_moves.append((self.loc[pv][1], "r", src))
                else:
                    a.mov_mr(self.va(pv), src)
        self.parallel_move(gp_moves)
        self.parallel_move(xmm_moves, float_regs=True)

        for i, ins in enumerate(f.ins):
            nxt = f.ins[i + 1] if i + 1 < len(f.ins) else None
            self.next_label = nxt.a if (nxt is not None and nxt.op == "label") \
                else None
            self.gen_ins(ins)
        a.ud2()

    def emit_branch(self, cc, lt, lf):
        """Emit a two-way branch, using fall-through wherever possible."""
        a = self.asm
        if self.next_label == lf:
            a.jcc(cc, lt)
        elif self.next_label == lt:
            a.jcc(INVERT_CC[cc], lf)
        else:
            a.jcc(cc, lt)
            a.jmp(lf)

    def epilogue(self):
        a = self.asm
        if self.frameless:
            if self.pad:
                a.alu_ri("+", RSP, self.pad)
            for r in reversed(self.callee):
                a.pop(r)
            a.ret()
            return
        for r in self.callee:
            a.mov_rm(r, Mem(RBP, self.save_off[r]))
        a.mov_rr(RSP, RBP)
        a.pop(RBP)
        a.ret()

    # --------------------------------------------------------- instructions
    def gen_ins(self, ins):
        a = self.asm
        op = ins.op
        f = self.f

        if op == "label":
            a.label(ins.a)
            return

        if op == "const":
            r = self.wreg(ins.a, RAX)
            a.mov_ri(r, ins.b)
            self.done(ins.a, r)
            return

        if op == "fconst":
            bits = ins.c
            if bits == 64:
                blob = struct.pack("<d", ins.b)
            else:
                blob = struct.pack("<f", ins.b) + b"\0\0\0\0"
            lbl = self.prog.add_ro(blob)
            x = self.wregf(ins.a, XT0)
            a.movsd_load(x, rip(lbl), 64)
            self.donef(ins.a, x)
            return

        if op == "mov":
            if ins.a in f.float_vregs or ins.b in f.float_vregs:
                x = self.rdf(ins.b, XT0)
                self.donef(ins.a, x)
            else:
                r = self.rd(ins.b, RAX)
                self.done(ins.a, r)
            return

        if op == "lea":
            r = self.wreg(ins.a, RAX)
            a.lea(r, Mem(RBP, ins.b.off))
            self.done(ins.a, r)
            return

        if op == "leaf":
            r = self.wreg(ins.a, RAX)
            a.lea(r, rip(ins.b))
            self.done(ins.a, r)
            return

        if op in ("leag", "leas"):
            r = self.wreg(ins.a, RAX)
            a.lea(r, rip(ins.b))
            self.done(ins.a, r)
            return

        if op == "bin":
            return self.gen_bin(ins)
        if op == "bini":
            return self.gen_bini(ins)

        if op == "un":
            d, o, s, ty = ins.a, ins.b, ins.c, ins.d
            x = self.rd(s, R10)
            r = self.wreg(d, R10)
            if r != x:
                a.mov_rr(r, x)
            if o == "-":
                a.neg(r)
            else:
                a.not_(r)
            self.narrow(r, ty)
            self.done(d, r)
            return

        if op in ("cmp", "cmpi"):
            d, o, signed = ins.a, ins.b, ins.e
            x = self.rd(ins.c, R10)
            if op == "cmpi":
                a.cmp_ri(x, ins.d)
            else:
                y = self.rd(ins.d, R11)
                a.alu_rr("cmp", x, y)
            cc = (SIGNED_CC if signed else UNSIGNED_CC)[o]
            a.setcc(cc, RAX)
            a.movzx(RAX, RAX, 1)
            self.done(d, RAX)
            return

        if op == "fcmp":
            d, o, bits = ins.a, ins.b, ins.e
            x = self.rdf(ins.c, XT0)
            y = self.rdf(ins.d, XT1)
            a.ucomis(x, y, bits)
            a.setcc(UNSIGNED_CC[o], RAX)
            a.movzx(RAX, RAX, 1)
            self.done(d, RAX)
            return

        if op == "fbin":
            d, o, bits = ins.a, ins.b, ins.e
            x = self.rdf(ins.c, XT0)
            y = self.rdf(ins.d, XT1)
            t = self.wregf(d, XT0)
            if t == y:
                t = XT0
                if t == y:
                    t = XT2
            if t != x:
                a.movsd_load(t, x, 64)
            a.fbin(o, t, y, bits)
            self.donef(d, t)
            return

        if op == "fun":
            d, bits = ins.a, ins.d
            x = self.rdf(ins.c, XT1)
            a.xorps(XT0, XT0)
            a.fbin("-", XT0, x, bits)
            self.donef(d, XT0)
            return

        if op == "load":
            d, addr, size, signed, isf = ins.a, ins.b, ins.c, ins.d, ins.e
            return self.emit_load(d, addr, 0, size, signed, isf)

        if op == "loadd":
            d, base, disp = ins.a, ins.b, ins.c
            size, signed, isf = ins.d
            return self.emit_load(d, base, disp, size, signed, isf)

        if op == "loadx":
            d, base = ins.a, ins.b
            i, scale, disp = ins.c
            size, signed, isf = ins.d
            bp = self.rd(base, R10)
            ip = self.rd(i, R11)
            return self.emit_load_mem(d, Mem(bp, disp, ip, scale), size,
                                      signed, isf)

        if op == "storex":
            base = ins.a
            i, scale, disp = ins.b
            val = ins.c
            size, isf = ins.d
            bp = self.rd(base, R10)
            ip = self.rd(i, R11)
            return self.emit_store_mem(Mem(bp, disp, ip, scale), val, size, isf)

        if op == "store":
            addr, val, size, isf = ins.a, ins.b, ins.c, ins.d
            return self.emit_store(addr, 0, val, size, isf)

        if op == "stored":
            base, disp, val = ins.a, ins.b, ins.c
            size, isf = ins.d
            return self.emit_store(base, disp, val, size, isf)

        if op == "memcpy":
            dst, src, n = ins.a, ins.b, ins.c
            if n == 0:
                return
            dk, dv = self.src_of(dst)
            sk, sv = self.src_of(src)
            self.parallel_move([(RDI, dk, dv), (RSI, sk, sv)])
            a.mov_ri(RCX, n)
            a.cld()
            a.rep_movsb()
            return

        if op == "memzero":
            addr, n = ins.a, ins.b
            if n == 0:
                return
            ak, av = self.src_of(addr)
            self.parallel_move([(RDI, ak, av)])
            a.mov_ri(RAX, 0)
            a.mov_ri(RCX, n)
            a.cld()
            a.rep_stosb()
            return

        if op == "jmp":
            if self.next_label != ins.a:
                a.jmp(ins.a)
            return

        if op == "br":
            c = self.rd(ins.a, RAX)
            a.test_rr(c, c)
            self.emit_branch("ne", ins.b, ins.c)
            return

        if op == "brc":
            o, x, y = ins.a, ins.b, ins.c
            signed, imm = ins.d
            lt, lf = ins.e
            xr = self.rd(x, R10)
            if y is None:
                a.cmp_ri(xr, imm)
            else:
                yr = self.rd(y, R11)
                a.alu_rr("cmp", xr, yr)
            cc = (SIGNED_CC if signed else UNSIGNED_CC)[o]
            self.emit_branch(cc, lt, lf)
            return

        if op == "ret":
            if ins.a is not None:
                if ins.b:
                    x = self.rdf(ins.a, XT0)
                    if x != 0:
                        a.movsd_load(0, x, 64)
                else:
                    r = self.rd(ins.a, RAX)
                    a.mov_rr(RAX, r)
            self.epilogue()
            return

        if op == "call":
            return self.gen_call(ins)

        if op == "calli":
            return self.gen_call(ins, indirect=True)

        if op == "syscall":
            d, num, args = ins.a, ins.b, ins.c
            moves = []
            for k, v in enumerate(args):
                kind, val = self.src_of(v)
                moves.append((SYS_ARG_REGS[k], kind, val))
            self.parallel_move(moves)
            a.mov_ri(RAX, num)
            a.syscall()
            self.done(d, RAX)
            return

        if op == "cvt":
            return self.gen_cvt(ins)

        if op == "rawbytes":
            a.raw(ins.a)
            return

        if op == "trap":
            a.ud2()
            return

        raise Exception("codegen: unhandled IR op %r" % op)

    # -------------------------------------------------------------- memory
    def emit_load(self, d, base, disp, size, signed, isf):
        p = self.rd(base, R10)
        return self.emit_load_mem(d, Mem(p, disp), size, signed, isf)

    def emit_load_mem(self, d, m, size, signed, isf):
        a = self.asm
        if isf:
            # an f32 value lives in the low 32 bits of its register and home,
            # so no conversion is needed on the way in or out of memory
            x = self.wregf(d, XT0)
            a.movsd_load(x, m, size * 8)
            self.donef(d, x)
            return
        r = self.wreg(d, RAX)
        if signed:
            a.movsx(r, m, size)
        else:
            a.movzx(r, m, size)
        self.done(d, r)

    def emit_store(self, base, disp, val, size, isf):
        p = self.rd(base, R10)
        return self.emit_store_mem(Mem(p, disp), val, size, isf)

    def emit_store_mem(self, m, val, size, isf):
        a = self.asm
        if isf:
            x = self.rdf(val, XT0)
            a.movsd_store(m, x, size * 8)
            return
        r = self.rd(val, RAX)
        a.store_sized(m, r, size)

    # ---------------------------------------------------------------- calls
    def gen_call(self, ins, indirect=False):
        a = self.asm
        d, name, args, argf, retf = ins.a, ins.b, ins.c, ins.d, ins.e
        if indirect:
            # park the target in rax, which is never allocated and never an
            # argument register, before the argument registers are set up
            tgt = self.rd(name, RAX)
            a.mov_rr(RAX, tgt)
        ints = 0
        flts = 0
        gp = []
        xmm = []
        for v, isf in zip(args, argf):
            kind, val = self.src_of(v)
            if isf:
                xmm.append((flts, kind, val))
                flts += 1
            else:
                gp.append((INT_ARG_REGS[ints], kind, val))
                ints += 1
        self.parallel_move(gp)
        self.parallel_move(xmm, float_regs=True)
        if indirect:
            a.call_r(RAX)
        else:
            a.call(name)
        if d is not None:
            if retf:
                self.donef(d, 0)
            else:
                self.done(d, RAX)

    # ----------------------------------------------------------- arithmetic
    def gen_bin(self, ins):
        a = self.asm
        d, o, ty = ins.a, ins.b, ins.e
        if o in ("/", "%"):
            signed = (ty.kind == "int" and ty.signed)
            y = self.rd(ins.d, R10)
            if y != R10:
                a.mov_rr(R10, y)
            x = self.rd(ins.c, RAX)
            a.mov_rr(RAX, x)
            if signed:
                a.cqo()
                a.idiv(R10)
            else:
                a.mov_ri(RDX, 0)
                a.div(R10)
            res = RAX if o == "/" else RDX
            self.narrow(res, ty)
            self.done(d, res)
            return
        if o in ("<<", ">>"):
            x = self.rd(ins.c, R10)
            cnt = self.rd(ins.d, RCX)
            if cnt != RCX:
                a.mov_rr(RCX, cnt)
            r = self.wreg(d, R10)
            if r == RCX:
                r = R10
            if r != x:
                a.mov_rr(r, x)
            kind = o
            if o == ">>" and not (ty.kind == "int" and ty.signed):
                kind = ">>u"
            a.shift_cl(kind, r)
            self.narrow(r, ty)
            self.done(d, r)
            return
        x = self.rd(ins.c, R10)
        y = self.rd(ins.d, R11)
        r = self.wreg(d, R10)
        if r == y:
            r = R10
            if r == y:
                r = R11 if x != R11 else R10
        if r != x:
            a.mov_rr(r, x)
        if o == "*":
            a.imul_rr(r, y)
        else:
            a.alu_rr(o, r, y)
        self.narrow(r, ty)
        self.done(d, r)

    def gen_bini(self, ins):
        a = self.asm
        d, o, k, ty = ins.a, ins.b, ins.d, ins.e
        x = self.rd(ins.c, R10)
        if o in ("+", "-") and self.loc[d][0] == "r":
            # a single lea covers add/sub-with-constant without touching flags
            disp = k if o == "+" else -k
            if -0x80000000 <= disp <= 0x7FFFFFFF:
                r = self.loc[d][1]
                a.lea(r, Mem(x, disp))
                self.narrow(r, ty)
                return
        r = self.wreg(d, R10)
        if o in ("<<", ">>"):
            if r != x:
                a.mov_rr(r, x)
            kind = o
            if o == ">>" and not (ty.kind == "int" and ty.signed):
                kind = ">>u"
            a.shift_imm(kind, r, k)
        elif o == "*":
            if is_pow2(k):
                if r != x:
                    a.mov_rr(r, x)
                a.shift_imm("<<", r, log2(k))
            else:
                a.imul_ri(r, x, k)
        else:
            if r != x:
                a.mov_rr(r, x)
            a.alu_ri(o, r, k)
        self.narrow(r, ty)
        self.done(d, r)

    def gen_cvt(self, ins):
        a = self.asm
        d, s, ft, tt = ins.a, ins.b, ins.c, ins.d
        if ft.kind == "float" and tt.kind == "float":
            x = self.rdf(s, XT0)
            t = self.wregf(d, XT0)
            if ft.bits == 64 and tt.bits == 32:
                a.cvtsd2ss(t, x)
            elif ft.bits == 32 and tt.bits == 64:
                a.cvtss2sd(t, x)
            elif t != x:
                a.movsd_load(t, x, 64)
            self.donef(d, t)
            return
        if ft.kind == "float":
            x = self.rdf(s, XT0)
            r = self.wreg(d, RAX)
            a.cvttsd2si(r, x, ft.bits)
            self.narrow(r, tt)
            self.done(d, r)
            return
        if tt.kind == "float":
            r = self.rd(s, RAX)
            t = self.wregf(d, XT0)
            a.cvtsi2sd(t, r, tt.bits)
            self.donef(d, t)
            return
        r0 = self.rd(s, RAX)
        r = self.wreg(d, RAX)
        if r != r0:
            a.mov_rr(r, r0)
        self.narrow(r, tt)
        self.done(d, r)


def compile_program(prog, opt=True):
    return CodeGen(prog, opt).run()
