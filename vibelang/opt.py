"""IR optimisation passes.

Deliberately small and verifiable: constant folding, copy propagation,
address-displacement folding into memory operands, and dead code elimination
to a fixpoint. Every pass preserves observable behaviour, so the test suite
can be run with and without them as an A/B oracle (`vibec -O0`).
"""

from .ir import Ins, Func

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
    if op in ("call", "syscall", "calli", "intr"):
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
    if op == "fbrc":
        return [ins.b, ins.c]
    if op == "ret":
        return [ins.a] if ins.a is not None else []
    if op in ("call", "syscall", "intr"):
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
    elif op == "fbrc":
        ins.b = m(ins.b)
        ins.c = m(ins.c)
    elif op == "ret":
        if ins.a is not None:
            ins.a = m(ins.a)
    elif op in ("call", "syscall", "intr"):
        ins.c = [m(x) for x in ins.c]
    elif op == "calli":
        ins.b = m(ins.b)
        ins.c = [m(x) for x in ins.c]


def def_counts(f):
    cnt = {}
    # a parameter is defined once on entry, before any instruction
    for (_n, _t, pv) in f.params:
        cnt[pv] = 1
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
            bits = ty.size * 8
            r &= (1 << bits) - 1
            # registers hold narrow signed values sign-extended
            if getattr(ty, "signed", False) and r >= (1 << (bits - 1)):
                r -= (1 << bits)
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
        if (cur.op == "fcmp" and nxt is not None and nxt.op == "br"
                and nxt.a == cur.a and uses.get(cur.a, 0) == 1):
            out.append(Ins("fbrc", cur.b, cur.c, cur.d, cur.e, (nxt.b, nxt.c)))
            i += 2
            changed = True
            continue
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


def dominators(blocks):
    """idom[b] for each block index (block 0 is the entry)."""
    n = len(blocks)
    preds = [[] for _ in range(n)]
    for i, b in enumerate(blocks):
        for sidx in b.succ:
            preds[sidx].append(i)
    # reverse postorder
    seen = [False] * n
    order = []

    def dfs(i):
        seen[i] = True
        for sidx in blocks[i].succ:
            if not seen[sidx]:
                dfs(sidx)
        order.append(i)
    import sys
    sys.setrecursionlimit(max(10000, n * 4))
    dfs(0)
    rpo = list(reversed(order))
    pos = {b: k for k, b in enumerate(rpo)}
    idom = [None] * n
    idom[0] = 0
    changed = True
    while changed:
        changed = False
        for b in rpo[1:]:
            cands = [p for p in preds[b] if idom[p] is not None]
            if not cands:
                continue
            new = cands[0]
            for p in cands[1:]:
                x, y = p, new
                while x != y:
                    while pos[x] > pos[y]:
                        x = idom[x]
                    while pos[y] > pos[x]:
                        y = idom[y]
                new = x
            if idom[b] != new:
                idom[b] = new
                changed = True
    return idom


def _cse_key(ins):
    op = ins.op
    if op == "bin":
        return ("bin", ins.b, ins.c, ins.d, str(ins.e))
    if op == "bini":
        return ("bini", ins.b, ins.c, ins.d, str(ins.e))
    if op == "un":
        return ("un", ins.b, ins.c, str(ins.d))
    if op == "cvt":
        return ("cvt", ins.b, str(ins.c), str(ins.d))
    if op == "const":
        return ("const", ins.b)
    if op == "fconst":
        return ("fconst", ins.b, ins.c)
    if op in ("leag", "leas", "leaf"):
        return (op, ins.b)
    if op == "lea":
        return ("lea", id(ins.b))
    if op in ("cmp", "fcmp"):
        return (op, ins.b, ins.c, ins.d, ins.e)
    if op == "cmpi":
        return (op, ins.b, ins.c, ins.d, ins.e)
    if op == "fbin":
        return (op, ins.b, ins.c, ins.d, ins.e)
    if op == "fun":
        return (op, ins.b, ins.c, ins.d)
    return None


def cse(f):
    """Common subexpression elimination over pure operations whose operands
    are defined exactly once (so their value never changes), reusing a
    result computed in a dominating block."""
    from .regalloc import build_blocks
    cnt = def_counts(f)
    blocks = build_blocks(f)
    if not blocks:
        return False
    idom = dominators(blocks)
    tables = [None] * len(blocks)
    mapping = {}
    drop = set()
    # blocks in index order: the entry first; a block's idom always has a
    # smaller index in this linear layout only when it precedes it, so
    # process in a dominator-tree preorder instead
    children = [[] for _ in blocks]
    for b in range(1, len(blocks)):
        if idom[b] is not None:
            children[idom[b]].append(b)
    stack = [0]
    tables[0] = {}
    while stack:
        b = stack.pop()
        table = tables[b]
        # values whose operands may change (loop counters) are reused only
        # within the block, up to the next write to an operand; constants
        # too, so a shared constant never has to live across a loop
        local = {}
        for k in range(blocks[b].start, blocks[b].end + 1):
            ins = f.ins[k]
            key = _cse_key(ins)
            ds = defs_of(ins)
            if ds:
                dd = ds[0]
                for lk in [lk for lk, (lv, ops) in local.items() if dd in ops]:
                    del local[lk]
            if key is None:
                continue
            d = ds[0]
            if cnt.get(d, 0) != 1:
                continue
            uses = list(uses_of(ins))
            stable = all(cnt.get(u, 0) == 1 for u in uses) \
                and ins.op not in ("const", "fconst")
            prev = table.get(key) if stable else None
            if prev is None and key in local:
                prev = local[key][0]
            if prev is not None:
                mapping[d] = prev
                drop.add(k)
            elif stable:
                table[key] = d
            else:
                local[key] = (d, set(uses))
        for c in children[b]:
            tables[c] = dict(table)
            stack.append(c)
    if not mapping:
        return False
    f.ins = [x for k, x in enumerate(f.ins) if k not in drop]
    for ins in f.ins:
        replace_uses(ins, mapping)
    return True


# operations whose low bits depend only on their operands' low bits
LOW_ONLY = {"+", "-", "*", "&", "|", "^", "<<"}


def skip_narrow(f):
    """A narrow-typed result feeding only low-bits-only operations of the
    same width (or a conversion to a width no wider) need not be sign- or
    zero-extended after every step: the consumer extends its own result."""
    uses = {}
    for ins in f.ins:
        for u in uses_of(ins):
            uses.setdefault(u, []).append(ins)
    changed = False
    for ins in f.ins:
        if ins.op not in ("bin", "bini") or ins.b not in LOW_ONLY:
            continue
        ty = ins.e
        if ty is None or ty.kind != "int" or ty.size == 8:
            continue
        us = uses.get(ins.a, [])
        if not us:
            continue
        good = True
        for u in us:
            if u.op in ("bin", "bini") and u.b in LOW_ONLY \
                    and u.e is not None and u.e.kind == "int" \
                    and u.e.size == ty.size and u.e.signed == ty.signed:
                continue
            if u.op == "cvt" and u.d.kind == "int" and u.d.size <= ty.size:
                continue
            good = False
            break
        if good:
            ins.e = None
            changed = True
    return changed


def coalesce_movs(f):
    """`op d, ...` immediately followed by `mov v, d`, with d used nowhere
    else: write the result straight into v. This is the shape every loop
    counter update has (`i = i + 1`)."""
    uses = {}
    for ins in f.ins:
        for u in uses_of(ins):
            uses[u] = uses.get(u, 0) + 1
    out = []
    changed = False
    i = 0
    n = len(f.ins)
    while i < n:
        cur = f.ins[i]
        nxt = f.ins[i + 1] if i + 1 < n else None
        if (nxt is not None and nxt.op == "mov" and cur.op in COALESCE
                and defs_of(cur) == [nxt.b] and uses.get(nxt.b, 0) == 1
                and nxt.a != nxt.b):
            cur.a = nxt.a
            out.append(cur)
            i += 2
            changed = True
            continue
        out.append(cur)
        i += 1
    f.ins = out
    return changed


COALESCE = {"bin", "bini", "un", "cvt", "fbin", "fun", "load", "loadd",
            "loadx", "const", "fconst", "lea", "leag", "leas", "leaf"}


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
HOISTABLE = {"bin", "bini", "un", "cvt", "lea", "leag", "leas", "fconst",
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
        elif x.op in ("brc", "fbrc"):
            tgts = list(x.e)
        elif x.op == "br":
            tgts = [x.b, x.c]
        for t in tgts:
            j = label_at.get(t)
            if j is not None and j < i:
                loops.append((j, i))
    # one loop per header, spanning to its furthest back-edge (`*>` adds
    # inner back-edges that would otherwise truncate the loop)
    best = {}
    for (j, i) in loops:
        best[j] = max(best.get(j, i), i)
    return sorted(best.items())


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
            # the pre-header: before the jump that enters the loop (a
            # rotated loop is entered by a jump to its test, which lies
            # inside the loop range)
            inside = set(x.a for x in f.ins[j:i + 1] if x.op == "label")
            p = j
            while p > 0 and f.ins[p - 1].op == "jmp" and f.ins[p - 1].a in inside:
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


def strength_reduce(f):
    """`t = i * K` inside a loop whose counter i steps by a constant becomes
    a running value u, stepped by c*K next to the counter: one add instead
    of a multiply per iteration."""
    changed = False
    for _ in range(8):
        loops = find_loops(f)
        if not loops:
            break
        loops.sort(key=lambda pr: pr[1] - pr[0])
        whole = def_counts(f)
        did = False
        for (j, i) in loops:
            body = f.ins[j:i + 1]
            dcount = {}
            for x in body:
                for d in defs_of(x):
                    dcount[d] = dcount.get(d, 0) + 1
            counters = {}      # v -> (index of its bini, step)
            for k in range(j, i + 1):
                x = f.ins[k]
                if (x.op == "bini" and x.b == "+" and x.a == x.c
                        and dcount.get(x.a, 0) == 1):
                    counters[x.a] = (k, x.d)
            if not counters:
                continue
            cands = []
            for k in range(j, i + 1):
                x = f.ins[k]
                if x.op == "bini" and x.b == "*" and x.c in counters \
                        and whole.get(x.a, 0) == 1:
                    cands.append((k, x.c, x.d, None))
                elif x.op == "bin" and x.b == "*" and whole.get(x.a, 0) == 1:
                    if x.c in counters and whole.get(x.d, 0) == 1 \
                            and x.d not in dcount:
                        cands.append((k, x.c, None, x.d))
                    elif x.d in counters and whole.get(x.c, 0) == 1 \
                            and x.c not in dcount:
                        cands.append((k, x.d, None, x.c))
            if not cands:
                continue
            # one running value per (counter, multiplier)
            groups = {}
            for (k, v, K, w) in cands:
                groups.setdefault((v, K, w), []).append(k)
            inside = set(x.a for x in body if x.op == "label")
            p = j
            while p > 0 and f.ins[p - 1].op == "jmp" and f.ins[p - 1].a in inside:
                p -= 1
            pre = []
            after = {}         # counter bini index -> instructions to add
            repl = {}
            for (v, K, w), ks in groups.items():
                ty = f.ins[ks[0]].e
                u = f.vreg()
                cidx, step = counters[v]
                if K is not None:
                    pre.append(Ins("bini", u, "*", v, K, ty))
                    after.setdefault(cidx, []).append(
                        Ins("bini", u, "+", u, step * K, ty))
                else:
                    pre.append(Ins("bin", u, "*", v, w, ty))
                    sv = f.vreg()
                    pre.append(Ins("bini", sv, "*", w, step, ty))
                    after.setdefault(cidx, []).append(
                        Ins("bin", u, "+", u, sv, ty))
                for k in ks:
                    repl[k] = Ins("mov", f.ins[k].a, u)
            out = []
            for k, x in enumerate(f.ins):
                if k == p:
                    out.extend(pre)
                out.append(repl.get(k, x))
                if k in after:
                    out.extend(after[k])
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


# ---- inlining ---------------------------------------------------------------
#
# Runs on the raw IR from the front end, before any other pass, so only the
# front end's instruction set has to be understood here.

# op -> (fields holding one vreg, fields holding a list of vregs)
_VFIELDS = {
    "const": ("a",), "fconst": ("a",), "mov": ("a", "b"), "lea": ("a",),
    "leaf": ("a",), "leag": ("a",), "leas": ("a",), "bin": ("a", "c", "d"),
    "un": ("a", "c"), "cmp": ("a", "c", "d"), "fcmp": ("a", "c", "d"),
    "fbin": ("a", "c", "d"), "fun": ("a", "c"), "load": ("a", "b"),
    "store": ("a", "b"), "memcpy": ("a", "b"), "memzero": ("a",),
    "br": ("a",), "ret": ("a",), "call": ("a",), "calli": ("a", "b"),
    "syscall": ("a",), "intr": ("a",), "cvt": ("a", "b"), "label": (), "jmp": (), "trap": (),
}
INLINE_MAX = 40          # callee size, in IR instructions
INLINE_GROWTH = 4000     # stop growing a caller past this


def _inlinable(f):
    if len(f.ins) > INLINE_MAX or f.name == "@!":
        return False
    return all(i.op in _VFIELDS for i in f.ins)


def _splice(caller, call, callee, serial):
    """IR for one inlined call: the callee body with fresh names."""
    vmap = {}

    def v(x):
        if x not in vmap:
            vmap[x] = caller.vreg(x in callee.float_vregs)
        return vmap[x]

    smap = {}
    lmap = {}

    def lab(name):
        if name not in lmap:
            lmap[name] = "%s$i%d_%s" % (name, serial, caller.name)
        return lmap[name]

    out = []
    done = lab(".inl_done")
    for (_, _, pv), arg in zip(callee.params, call.c):
        out.append(Ins("mov", v(pv), arg))
    for i in callee.ins:
        if i.op == "ret":
            if i.a is not None and call.a is not None:
                out.append(Ins("mov", call.a, v(i.a)))
            out.append(Ins("jmp", done))
            continue
        n = Ins(i.op, i.a, i.b, i.c, i.d, i.e)
        for fld in _VFIELDS[i.op]:
            x = getattr(n, fld)
            if x is not None:
                setattr(n, fld, v(x))
        if i.op in ("call", "calli", "syscall", "intr"):
            n.c = [v(x) for x in i.c]
        if i.op == "lea":
            if i.b.idx not in smap:
                smap[i.b.idx] = caller.slot(i.b.size, i.b.align, i.b.name)
            n.b = smap[i.b.idx]
        elif i.op in ("label", "jmp"):
            n.a = lab(i.a)
        elif i.op == "br":
            n.b, n.c = lab(i.b), lab(i.c)
        out.append(n)
    out.append(Ins("label", done))
    return out


def inline(prog):
    """Two rounds, each inlining the bodies as they stood when the round
    began; a self-recursive function is therefore unrolled a fixed number of
    times and no more."""
    serial = 0
    for _ in range(2):
        snap = {}
        for f in prog.funcs:
            if _inlinable(f):
                c = Func(f.name, f.params, f.ret, f.sret)
                c.ins = list(f.ins)
                c.float_vregs = set(f.float_vregs)
                c.calls = f.calls
                snap[f.name] = c
        for f in prog.funcs:
            if not any(i.op == "call" and i.b in snap for i in f.ins):
                continue
            out = []
            for i in f.ins:
                if (i.op == "call" and i.b in snap
                        and len(out) < INLINE_GROWTH):
                    serial += 1
                    callee = snap[i.b]
                    out.extend(_splice(f, i, callee, serial))
                    f.calls = f.calls or callee.calls
                else:
                    out.append(i)
            f.ins = out
    return prune(prog)


def optimise(prog):
    inline(prog)
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
            c |= cse(f)
            c |= coalesce_movs(f)
            c |= skip_narrow(f)
            c |= fuse_branches(f)
            c |= clean_labels(f)
            c |= licm(f)
            c |= strength_reduce(f)
            if not c:
                break
    return prog
