"""Linear-scan register allocation over the VIBE IR.

Liveness is computed with a proper backward dataflow fixpoint on the control
flow graph, then intervals are widened to cover every block in which a value
is live. Blocks are emitted in source order, so a loop occupies a contiguous
index range and loop-carried values get correct (conservative) intervals.

Values that are live across a call-like instruction are confined to
callee-saved registers; float values live across one are spilled, since the
SysV ABI preserves no xmm register.
"""

from .opt import defs_of, uses_of
from .x64 import RAX, RCX, RDX, RBX, RSI, RDI, R8, R9, R12, R13, R14, R15

# r10/r11 stay free as scratch; rax/rcx/rdx are implicit in div, shifts,
# setcc, syscalls and return values, so they are never allocated.
GP_POOL = [RBX, R12, R13, R14, R15, RSI, RDI, R8, R9]
GP_CALLEE = [RBX, R12, R13, R14, R15]
CALLEE_SAVED = set(GP_CALLEE)

# xmm0-xmm2 are scratch in the code generator.
XMM_POOL = list(range(3, 14))

CALL_LIKE = {"call", "syscall", "calli", "memcpy", "memzero"}

INT_ARG_REGS = [RDI, RSI, RDX, RCX, R8, R9]


def build_hints(f):
    """Register preferences that let moves disappear.

    `same[d] = s` asks for d and s to share a register, which removes the
    `mov d, s` that would otherwise start a two-operand instruction.
    `phys[v] = r` asks for the ABI register a value is about to be passed in.
    """
    same = {}
    phys = {}
    # a parameter already sits in its ABI register on entry; asking for that
    # same register removes the entry shuffle entirely
    k = 0
    for (_, pty, pv) in f.params:
        if pty.kind != "float":
            if k < len(INT_ARG_REGS):
                phys.setdefault(pv, INT_ARG_REGS[k])
            k += 1
    for ins in f.ins:
        if ins.op in ("bin", "bini") and ins.a is not None:
            same.setdefault(ins.a, ins.c)
        elif ins.op == "mov":
            same.setdefault(ins.a, ins.b)
        elif ins.op in ("un", "cvt"):
            src = ins.c if ins.op == "un" else ins.b
            same.setdefault(ins.a, src)
        elif ins.op in ("call", "calli"):
            k = 0
            for v, isf in zip(ins.c, ins.d):
                if not isf:
                    if k < len(INT_ARG_REGS):
                        phys.setdefault(v, INT_ARG_REGS[k])
                    k += 1
    return same, phys


class Block:
    __slots__ = ("start", "end", "succ", "live_in", "live_out")

    def __init__(self, start):
        self.start = start
        self.end = start
        self.succ = []
        self.live_in = set()
        self.live_out = set()


def build_blocks(f):
    ins = f.ins
    n = len(ins)
    starts = {0}
    label_at = {}
    for i, x in enumerate(ins):
        if x.op == "label":
            starts.add(i)
            label_at[x.a] = i
        if x.op in ("jmp", "br", "brc", "ret") and i + 1 < n:
            starts.add(i + 1)
    ordered = sorted(starts)
    blocks = []
    index_of = {}
    for k, s in enumerate(ordered):
        e = (ordered[k + 1] - 1) if k + 1 < len(ordered) else n - 1
        b = Block(s)
        b.end = e
        index_of[s] = len(blocks)
        blocks.append(b)
    for k, b in enumerate(blocks):
        last = ins[b.end]
        if last.op == "jmp":
            t = label_at.get(last.a)
            if t is not None:
                b.succ.append(index_of[t])
        elif last.op == "br":
            for tgt in (last.b, last.c):
                t = label_at.get(tgt)
                if t is not None:
                    b.succ.append(index_of[t])
        elif last.op == "brc":
            for tgt in last.e:
                t = label_at.get(tgt)
                if t is not None:
                    b.succ.append(index_of[t])
        elif last.op == "ret":
            pass
        else:
            if k + 1 < len(blocks):
                b.succ.append(k + 1)
    return blocks


def liveness(f, blocks):
    ins = f.ins
    gen = []
    kill = []
    for b in blocks:
        g, k = set(), set()
        for i in range(b.start, b.end + 1):
            for u in uses_of(ins[i]):
                if u not in k:
                    g.add(u)
            for d in defs_of(ins[i]):
                k.add(d)
        gen.append(g)
        kill.append(k)
    changed = True
    while changed:
        changed = False
        for i in range(len(blocks) - 1, -1, -1):
            b = blocks[i]
            out = set()
            for s in b.succ:
                out |= blocks[s].live_in
            inn = gen[i] | (out - kill[i])
            if out != b.live_out or inn != b.live_in:
                b.live_out = out
                b.live_in = inn
                changed = True


def intervals(f, blocks):
    ins = f.ins
    start = {}
    end = {}

    def touch(v, i):
        if v not in start:
            start[v] = i
            end[v] = i
        else:
            if i < start[v]:
                start[v] = i
            if i > end[v]:
                end[v] = i

    for (_, _, pv) in f.params:
        touch(pv, 0)
    for i, x in enumerate(ins):
        for u in uses_of(x):
            touch(u, i)
        for d in defs_of(x):
            touch(d, i)
    # A value live on entry to a block is live from its first instruction; a
    # value live on exit is live to its last. Widening on the union of the
    # two would stretch every live-in value to the end of the block even
    # when it dies half way through.
    for b in blocks:
        for v in b.live_in:
            touch(v, b.start)
        for v in b.live_out:
            touch(v, b.end)
    return start, end


def allocate(f):
    """Returns {vreg: ('r', reg) | ('x', xmm) | ('m',)} and the set of
    callee-saved registers that must be preserved."""
    blocks = build_blocks(f)
    liveness(f, blocks)
    start, end = intervals(f, blocks)

    call_idx = [i for i, x in enumerate(f.ins) if x.op in CALL_LIKE]

    def crosses(v):
        s, e = start[v], end[v]
        for i in call_idx:
            if s < i < e:
                return True
        return False

    same, phys = build_hints(f)
    order = sorted(start.keys(), key=lambda v: (start[v], end[v]))
    loc = {}
    active = []          # list of (end, vreg, reg, is_float)
    free_gp = list(GP_POOL)
    free_xmm = list(XMM_POOL)
    used_callee = set()

    def expire(at):
        nonlocal active
        keep = []
        for (e, v, r, isf) in active:
            if e < at:
                (free_xmm if isf else free_gp).append(r)
            else:
                keep.append((e, v, r, isf))
        active = keep

    for v in order:
        expire(start[v])
        isf = v in f.float_vregs
        x = crosses(v)
        if isf:
            if x:
                loc[v] = ("m",)
                continue
            pool = [r for r in free_xmm]
            if not pool:
                loc[v] = ("m",)
                continue
            r = pool[0]
            free_xmm.remove(r)
            loc[v] = ("x", r)
            active.append((end[v], v, r, True))
            continue
        cands = [r for r in free_gp if (not x) or r in CALLEE_SAVED]
        if not cands:
            # nothing free: evict the active value whose live range ends
            # furthest away, which is the one that benefits least from a
            # register (classic linear-scan spill heuristic)
            best = None
            for k2, (e2, v2, r2, f2) in enumerate(active):
                if f2:
                    continue
                if x and r2 not in CALLEE_SAVED:
                    continue
                if best is None or e2 > active[best][0]:
                    best = k2
            if best is not None and active[best][0] > end[v]:
                e2, v2, r2, f2 = active.pop(best)
                loc[v2] = ("m",)
                loc[v] = ("r", r2)
                if r2 in CALLEE_SAVED:
                    used_callee.add(r2)
                active.append((end[v], v, r2, False))
                continue
            loc[v] = ("m",)
            continue
        # honour a coalescing hint when it is available, otherwise prefer
        # caller-saved registers for short-lived values so the callee-saved
        # ones stay free for values that really need them
        hint = None
        s_src = same.get(v)
        if s_src is not None and loc.get(s_src, ("m",))[0] == "r":
            cand = loc[s_src][1]
            if cand in cands:
                hint = cand
            elif end.get(s_src, -1) <= start[v] and (
                    (not x) or cand in CALLEE_SAVED):
                # the source dies exactly here and the generated sequence
                # reads it before writing the destination, so the register
                # can be reused directly
                for k2, (e2, v2, r2, f2) in enumerate(active):
                    if v2 == s_src and r2 == cand:
                        active.pop(k2)
                        free_gp.append(cand)
                        hint = cand
                        break
        if hint is None:
            p = phys.get(v)
            if p is not None and p in cands:
                hint = p
        if hint is not None:
            r = hint
        else:
            if not x:
                pref = [r2 for r2 in cands if r2 not in CALLEE_SAVED] or cands
            else:
                pref = cands
            r = pref[0]
        free_gp.remove(r)
        loc[v] = ("r", r)
        if r in CALLEE_SAVED:
            used_callee.add(r)
        active.append((end[v], v, r, False))

    for v in range(f.nvreg):
        loc.setdefault(v, ("m",))
    return loc, sorted(used_callee)


def all_memory(f):
    return {v: ("m",) for v in range(f.nvreg)}, []
