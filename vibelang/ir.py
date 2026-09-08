"""VIBE mid-level IR.

Linear, virtual-register based, with explicit stack slots. Aggregates always
live in memory; an aggregate-typed IR value is the *address* of that memory.
"""


class Slot:
    __slots__ = ("idx", "size", "align", "off", "name")

    def __init__(self, idx, size, align, name=""):
        self.idx = idx
        self.size = size
        self.align = align
        self.off = 0
        self.name = name


class Ins:
    __slots__ = ("op", "a", "b", "c", "d", "e")

    def __init__(self, op, a=None, b=None, c=None, d=None, e=None):
        self.op = op
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

    def __repr__(self):
        parts = [self.op]
        for x in (self.a, self.b, self.c, self.d, self.e):
            if x is not None:
                parts.append(repr(x))
        return " ".join(parts)


class Func:
    def __init__(self, name, params, ret, sret):
        self.name = name
        self.params = params        # [(name, Type, vreg_or_slot)]
        self.ret = ret
        self.sret = sret            # True when the return value is aggregate
        self.ins = []
        self.slots = []
        self.nvreg = 0
        self.nlabel = 0
        self.frame = 0
        self.float_vregs = set()
        self.calls = False

    def vreg(self, is_float=False):
        v = self.nvreg
        self.nvreg += 1
        if is_float:
            self.float_vregs.add(v)
        return v

    def slot(self, size, align, name=""):
        s = Slot(len(self.slots), size, align, name)
        self.slots.append(s)
        return s

    def label(self, hint="L"):
        self.nlabel += 1
        return ".%s%d_%s" % (hint, self.nlabel, self.name.replace("@!", "start"))

    def emit(self, op, *args):
        i = Ins(op, *args)
        self.ins.append(i)
        return i

    def dump(self):
        out = ["fn %s(%s) -> %s%s" % (
            self.name,
            ", ".join("%s:%s" % (p[0], p[1]) for p in self.params),
            self.ret, " [sret]" if self.sret else "")]
        for i in self.ins:
            out.append(("  " if i.op != "label" else "") + repr(i))
        return "\n".join(out)


class Program:
    def __init__(self):
        self.funcs = []
        self.globals = {}       # name -> (Type, bytes_or_None, is_bss)
        self.rodata = []        # list of (label, bytes)
        self.entry = None
        self._strn = 0

    def add_ro(self, data):
        for lbl, d in self.rodata:
            if d == data:
                return lbl
        lbl = "$ro%d" % self._strn
        self._strn += 1
        self.rodata.append((lbl, data))
        return lbl

    def dump(self):
        return "\n\n".join(f.dump() for f in self.funcs)
