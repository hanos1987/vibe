"""IR optimisation passes.

Deliberately small and verifiable: constant folding, copy propagation,
address-displacement folding into memory operands, and dead code elimination
to a fixpoint. Every pass preserves observable behaviour, so the test suite
can be run with and without them as an A/B oracle (`vibec -O0`).
"""

from .ir import Ins

PURE = {"const", "fconst", "mov", "lea", "leag", "leas", "bin", "un", "cmp",
        "fcmp", "fbin", "fun", "load", "loadd", "loadx", "cvt", "lea_idx",
        "bini", "cmpi", "leaf"}

INT_FOLD = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "&": lambda a, b: a & b,
    "|": lambda a, b: a | b,
    "^": lambda a, b: a ^ b,
    "<<": lambda a, b: a << b if 0 <= b < 64 else None,
}


def defs_of(ins):
    op = ins.op
    if op in ("const", "fconst", "mov", "lea", "leag", "leas", "bin", "un",
              "cmp", "fcmp", "fbin", "fun", "load", "cvt", "lea_idx",
              "bini", "cmpi"):
        return [ins.a]
    if op in ("loadd", "loadx"):
        return [ins.a]
    if op in ("call", "syscall", "calli"):
        return [ins.a] if ins.a is not None else []
    if op == "leaf":
        return [ins.a]
    return []


def uses_of(ins):
    op = ins.op
    if op == "mov":
        return [ins.b]
    if op in ("bin", "cmp", "fcmp", "fbin"):
        return [ins.c, ins.d]
    if op in ("bini", "cmpi"):
        return [ins.c]
    if op in ("un", "fun", "cvt"):
        return [ins.b] if op == "cvt" else [ins.c]
    if op == "load":
        return [ins.b]
    if op == "loadd":
        return [ins.b]
    if op == "loadx":
        return [ins.b, ins.c[0]]
    if op == "storex":
        return [ins.a, ins.b[0], ins.c]
    if op == "store":
        return [ins.a, ins.b]
    if op == "stored":
        return [ins.a, ins.c]
    if op == "lea_idx":
        return [ins.b, ins.c]
    if op == "memcpy":
        return [ins.a, ins.b]
    if op == "memzero":
        return [ins.a]
    if op == "br":
        return [ins.a]
    if op == "brc":
        return [ins.b] if ins.c is None else [ins.b, ins.c]
    if op == "ret":
        return [ins.a] if ins.a is not None else []
    if op in ("call", "syscall"):
        return list(ins.c)
    if op == "calli":
        return [ins.b] + list(ins.c)
    return []


def replace_uses(ins, mapping):
    op = ins.op

    def m(v):
        return mapping.get(v, v)

    if op == "mov":
        ins.b = m(ins.b)
    elif op in ("bin", "cmp", "fcmp", "fbin"):
        ins.c = m(ins.c)
        ins.d = m(ins.d)
    elif op in ("un", "fun", "bini", "cmpi"):
        ins.c = m(ins.c)
    elif op == "cvt":
        ins.b = m(ins.b)
    elif op in ("load", "loadd"):
        ins.b = m(ins.b)
    elif op == "store":
        ins.a = m(ins.a)
        ins.b = m(ins.b)
    elif op == "stored":
        ins.a = m(ins.a)
        ins.c = m(ins.c)
    elif op == "loadx":
        ins.b = m(ins.b)
        ins.c = (m(ins.c[0]), ins.c[1], ins.c[2])
    elif op == "storex":
        ins.a = m(ins.a)
        ins.b = (m(ins.b[0]), ins.b[1], ins.b[2])
        ins.c = m(ins.c)
    elif op == "lea_idx":
        ins.b = m(ins.b)
        ins.c = m(ins.c)
    elif op == "memcpy":
        ins.a = m(ins.a)
        ins.b = m(ins.b)
    elif op == "memzero":
        ins.a = m(ins.a)
    elif op == "br":
        ins.a = m(ins.a)
    elif op == "brc":
        ins.b = m(ins.b)
        if ins.c is not None:
            ins.c = m(ins.c)
    elif op == "ret":
        if ins.a is not None:
            ins.a = m(ins.a)
    elif op in ("call", "syscall"):
        ins.c = [m(x) for x in ins.c]
    elif op == "calli":
        ins.b = m(ins.b)
        ins.c = [m(x) for x in ins.c]


def def_counts(f):
    cnt = {}
    for ins in f.ins:
        for d in defs_of(ins):
            cnt[d] = cnt.get(d, 0) + 1
    return cnt


def single_def_consts(f):
    """vreg -> integer value, for vregs defined exactly once by `const`."""
    cnt = def_counts(f)
    out = {}
    for ins in f.ins:
        if ins.op == "const" and cnt.get(ins.a, 0) == 1:
            out[ins.a] = ins.b
    return out


def _signed(v):
    v &= 0xFFFFFFFFFFFFFFFF
    return v - (1 << 64) if v >= (1 << 63) else v


def fold_constants(f):
    changed = False
    for _ in range(4):
        consts = single_def_consts(f)
        cnt = def_counts(f)
        local = False
        for ins in f.ins:
            if ins.op != "bin" or cnt.get(ins.a, 0) != 1:
                continue
            if ins.c not in consts or ins.d not in consts:
                continue
            fn = INT_FOLD.get(ins.b)
            if fn is None:
                continue
            r = fn(_signed(consts[ins.c]), _signed(consts[ins.d]))
            if r is None:
                continue
            ty = ins.e
            r &= (1 << 64) - 1
            if ty is not None and getattr(ty, "size", 8) < 8:
                mask = (1 << (ty.size * 8)) - 1
                r &= mask
                if getattr(ty, "signed", False) and (r >> (ty.size * 8 - 1)) & 1:
                    r -= (1 << (ty.size * 8))
                    r &= (1 << 64) - 1
            ins.op = "const"
            ins.b = r
            ins.c = ins.d = ins.e = None
            local = changed = True
        if not local:
            break
    return changed


def fold_unary(f):
    changed = False
    consts = single_def_consts(f)
    cnt = def_counts(f)
    for ins in f.ins:
        if ins.op != "un" or cnt.get(ins.a, 0) != 1:
            continue
        if ins.c not in consts:
            continue
        a = _signed(consts[ins.c])
        r = (-a) if ins.b == "-" else (~a)
        ty = ins.d
        r &= (1 << 64) - 1
        if ty is not None and getattr(ty, "size", 8) < 8:
            r &= (1 << (ty.size * 8)) - 1
        ins.op = "const"
        ins.b = r
        ins.c = ins.d = ins.e = None
        changed = True
    return changed


def copy_propagate(f):
    """`mov d, s` where both d and s are defined exactly once: use s directly."""
    cnt = def_counts(f)
    mapping = {}
    for ins in f.ins:
        if (ins.op == "mov" and cnt.get(ins.a, 0) == 1
                and cnt.get(ins.b, 0) == 1):
            src = ins.b
            while src in mapping:
                src = mapping[src]
            if src != ins.a:
                mapping[ins.a] = src
    if not mapping:
        return False
    for ins in f.ins:
        replace_uses(ins, mapping)
    # the mov instructions themselves become dead and DCE removes them
    return True


def fold_addresses(f):
    """`t = base + K` feeding a load/store becomes a displacement."""
    consts = single_def_consts(f)
    cnt = def_counts(f)
    disp = {}
    for ins in f.ins:
        if (ins.op == "bin" and ins.b == "+" and cnt.get(ins.a, 0) == 1
                and ins.d in consts):
            k = _signed(consts[ins.d])
            if -0x80000000 <= k <= 0x7FFFFFFF:
                disp[ins.a] = (ins.c, k)
    if not disp:
        return False
    changed = False
    for ins in f.ins:
        if ins.op == "load" and ins.b in disp:
            base, k = disp[ins.b]
            ins.op = "loadd"
            ins.a, ins.b, ins.c, ins.d, ins.e = (
                ins.a, base, k, (ins.c, ins.d, ins.e), None)
            changed = True
        elif ins.op == "store" and ins.a in disp:
            base, k = disp[ins.a]
            ins.op = "stored"
            ins.a, ins.b, ins.c, ins.d, ins.e = (
                base, k, ins.b, (ins.c, ins.d), None)
            changed = True
    return changed


IMM_OPS = {"+", "-", "&", "|", "^", "*", "<<", ">>"}


def use_immediates(f):
    """Rewrite `op a, K` into an immediate form so the constant needs no
    register."""
    consts = single_def_consts(f)
    changed = False
    for ins in f.ins:
        if ins.op == "bin" and ins.b in IMM_OPS and ins.d in consts:
            k = _signed(consts[ins.d])
            if not (-0x80000000 <= k <= 0x7FFFFFFF):
                continue
            if ins.b in ("<<", ">>") and not (0 <= k < 64):
                continue
            ins.op = "bini"
            ins.d = k
            changed = True
        elif ins.op == "cmp" and ins.d in consts:
            k = _signed(consts[ins.d])
            if not (-0x80000000 <= k <= 0x7FFFFFFF):
                continue
            ins.op = "cmpi"
            ins.d = k
            changed = True
    return changed


def fuse_index(f):
    """`base + (i * K)` feeding a load or store becomes a scaled-index
    memory operand, which x86 addressing gives away for free."""
    cnt = def_counts(f)
    scale = {}
    for ins in f.ins:
        if (ins.op == "bini" and ins.b == "*" and ins.d in (1, 2, 4, 8)
                and cnt.get(ins.a, 0) == 1):
            scale[ins.a] = (ins.c, ins.d)
    idx = {}
    for ins in f.ins:
        if ins.op == "bin" and ins.b == "+" and cnt.get(ins.a, 0) == 1:
            if ins.d in scale:
                idx[ins.a] = (ins.c, scale[ins.d])
            elif ins.c in scale:
                idx[ins.a] = (ins.d, scale[ins.c])
    if not idx:
        return False
    changed = False
    for ins in f.ins:
        if ins.op == "load" and ins.b in idx:
            base, (i, k) = idx[ins.b]
            ins.op = "loadx"
            ins.a, ins.b, ins.c, ins.d, ins.e = (
                ins.a, base, (i, k, 0), (ins.c, ins.d, ins.e), None)
            changed = True
        elif ins.op == "store" and ins.a in idx:
            base, (i, k) = idx[ins.a]
            ins.op = "storex"
            ins.a, ins.b, ins.c, ins.d, ins.e = (
                base, (i, k, 0), ins.b, (ins.c, ins.d), None)
            changed = True
    return changed


def fuse_branches(f):
    """A comparison immediately feeding the branch that consumes it becomes a
    single conditional jump: no setcc, no movzx, no test, no register."""
    uses = {}
    for ins in f.ins:
        for u in uses_of(ins):
            uses[u] = uses.get(u, 0) + 1
    out = []
    i = 0
    n = len(f.ins)
    changed = False
    while i < n:
        cur = f.ins[i]
        nxt = f.ins[i + 1] if i + 1 < n else None
        if (cur.op in ("cmp", "cmpi") and nxt is not None and nxt.op == "br"
                and nxt.a == cur.a and uses.get(cur.a, 0) == 1):
            if cur.op == "cmp":
                b = Ins("brc", cur.b, cur.c, cur.d, (cur.e, None),
                        (nxt.b, nxt.c))
            else:
                b = Ins("brc", cur.b, cur.c, None, (cur.e, cur.d),
                        (nxt.b, nxt.c))
            out.append(b)
            i += 2
            changed = True
            continue
        out.append(cur)
        i += 1
    f.ins = out
    return changed


def dce(f):
    changed = False
    while True:
        used = set()
        for ins in f.ins:
            for u in uses_of(ins):
                used.add(u)
        keep = []
        dropped = False
        for ins in f.ins:
            if ins.op in PURE:
                ds = defs_of(ins)
                if ds and ds[0] not in used:
                    dropped = True
                    continue
            keep.append(ins)
        f.ins = keep
        if not dropped:
            return changed
        changed = True


# `const` is deliberately absent: materialising a constant costs one
# instruction, while keeping it live across a loop costs a register.
HOISTABLE = {"bin", "bini", "un", "cvt", "lea", "leag", "leas",
             "fbin", "cmp", "cmpi", "fcmp"}


def find_loops(f):
    ins = f.ins
    label_at = {}
    for i, x in enumerate(ins):
        if x.op == "label":
            label_at[x.a] = i
    loops = []
    for i, x in enumerate(ins):
        tgts = []
        if x.op == "jmp":
            tgts = [x.a]
        elif x.op == "brc":
            tgts = list(x.e)
        elif x.op == "br":
            tgts = [x.b, x.c]
        for t in tgts:
            j = label_at.get(t)
            if j is not None and j < i:
                loops.append((j, i))
    return loops


def licm(f):
    """Hoist loop-invariant pure computations into the pre-header.

    Only values with a single definition in the whole function are moved, so
    no earlier use can observe the change, and nothing that can trap or fault
    (division, memory reads) is hoisted out of the guard that protects it.
    """
    changed = False
    for _ in range(8):
        loops = find_loops(f)
        if not loops:
            break
        loops.sort(key=lambda pr: pr[1] - pr[0])
        whole = def_counts(f)
        did = False
        for (j, i) in loops:
            dcount = {}
            for x in f.ins[j:i + 1]:
                for d in defs_of(x):
                    dcount[d] = dcount.get(d, 0) + 1
            move = []
            for k in range(j, i + 1):
                x = f.ins[k]
                if x.op not in HOISTABLE:
                    continue
                if x.op in ("bin", "bini") and x.b in ("/", "%"):
                    continue
                ds = defs_of(x)
                if len(ds) != 1 or whole.get(ds[0], 0) != 1:
                    continue
                if any(u in dcount for u in uses_of(x)):
                    continue
                move.append(k)
            if not move:
                continue
            p = j
            while p > 0 and f.ins[p - 1].op == "jmp" and f.ins[p - 1].a == f.ins[j].a:
                p -= 1
            mset = set(move)
            moved = [f.ins[k] for k in move]
            out = []
            for k, x in enumerate(f.ins):
                if k == p:
                    out.extend(moved)
                if k in mset:
                    continue
                out.append(x)
            f.ins = out
            did = changed = True
            break
        if not did:
            break
    return changed


def clean_labels(f):
    """Drop `jmp L` immediately followed by `label L`."""
    out = []
    n = len(f.ins)
    for i, ins in enumerate(f.ins):
        if (ins.op == "jmp" and i + 1 < n and f.ins[i + 1].op == "label"
                and f.ins[i + 1].a == ins.a):
            continue
        out.append(ins)
    changed = len(out) != len(f.ins)
    f.ins = out
    return changed


def prune(prog):
    """Drop functions that cannot be reached from the entry point, so a
    program pays only for the library functions it actually uses."""
    byname = {f.name: f for f in prog.funcs}
    seen = set()
    stack = ["@!"]
    while stack:
        n = stack.pop()
        if n in seen or n not in byname:
            continue
        seen.add(n)
        for ins in byname[n].ins:
            if ins.op in ("call", "leaf"):
                stack.append(ins.b)
    prog.funcs = [f for f in prog.funcs if f.name in seen]
    return prog


def optimise(prog):
    for f in prog.funcs:
        for _ in range(3):
            c = False
            c |= fold_constants(f)
            c |= fold_unary(f)
            c |= copy_propagate(f)
            c |= fold_addresses(f)
            c |= use_immediates(f)
            c |= fuse_index(f)
            c |= dce(f)
            c |= fuse_branches(f)
            c |= clean_labels(f)
            c |= licm(f)
            if not c:
                break
    return prog
