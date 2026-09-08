"""VIBE type system.

Type notation (notation, not words):
  s8 s16 s32 s64   signed integers
  u8 u16 u32 u64   unsigned integers
  f32 f64          floats
  b                bool   (1 byte, 0 or 1)
  v                void
  *T               pointer to T
  [N]T             array of N T
  %Name            named struct or sum type
"""


class Type:
    kind = "?"
    size = 0
    align = 1

    def __eq__(self, o):
        return isinstance(o, Type) and str(self) == str(o)

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash(str(self))

    @property
    def is_scalar(self):
        return self.kind in ("int", "bool", "ptr", "float", "fn")

    @property
    def is_agg(self):
        return self.kind in ("arr", "struct", "sum")


class VoidT(Type):
    kind = "void"
    size = 0
    align = 1

    def __str__(self):
        return "v"


class BoolT(Type):
    kind = "bool"
    size = 1
    align = 1

    def __str__(self):
        return "b"


class IntT(Type):
    kind = "int"

    def __init__(self, bits, signed):
        self.bits = bits
        self.signed = signed
        self.size = bits // 8
        self.align = self.size

    def __str__(self):
        return ("s" if self.signed else "u") + str(self.bits)


class FloatT(Type):
    kind = "float"

    def __init__(self, bits):
        self.bits = bits
        self.size = bits // 8
        self.align = self.size

    def __str__(self):
        return "f" + str(self.bits)


class PtrT(Type):
    kind = "ptr"
    size = 8
    align = 8

    def __init__(self, to):
        self.to = to

    def __str__(self):
        return "*" + str(self.to)


class ArrT(Type):
    kind = "arr"

    def __init__(self, elem, n):
        self.elem = elem
        self.n = n

    @property
    def size(self):
        return self.elem.size * self.n

    @property
    def align(self):
        return self.elem.align

    def __str__(self):
        return "[%d]%s" % (self.n, self.elem)


class StructT(Type):
    kind = "struct"

    def __init__(self, name):
        self.name = name
        self.fields = []      # list of (name, type, offset)
        self.size = 0
        self.align = 1
        self.complete = False

    def field(self, name):
        for f in self.fields:
            if f[0] == name:
                return f
        return None

    def layout(self, fields):
        off = 0
        align = 1
        out = []
        for (fn, ft) in fields:
            a = ft.align or 1
            if off % a:
                off += a - (off % a)
            out.append((fn, ft, off))
            off += ft.size
            if a > align:
                align = a
        if off % align:
            off += align - (off % align)
        self.fields = out
        self.size = off
        self.align = align
        self.complete = True

    def __str__(self):
        return "%" + self.name


class SumT(Type):
    """Tagged union. Layout: s64 tag at offset 0, payload after."""
    kind = "sum"

    def __init__(self, name):
        self.name = name
        self.variants = []    # list of (name, [types], [offsets])
        self.size = 8
        self.align = 8
        self.complete = False

    def variant(self, name):
        for i, v in enumerate(self.variants):
            if v[0] == name:
                return i, v
        return None, None

    def layout(self, variants):
        biggest = 0
        align = 8
        out = []
        for (vn, vts) in variants:
            off = 8
            offs = []
            for t in vts:
                a = t.align or 1
                if off % a:
                    off += a - (off % a)
                offs.append(off)
                off += t.size
                if a > align:
                    align = a
            out.append((vn, vts, offs))
            if off > biggest:
                biggest = off
        if biggest < 8:
            biggest = 8
        if biggest % align:
            biggest += align - (biggest % align)
        self.variants = out
        self.size = biggest
        self.align = align
        self.complete = True

    def __str__(self):
        return "%" + self.name


class FnT(Type):
    kind = "fn"
    size = 8
    align = 8

    def __init__(self, params, ret):
        self.params = params
        self.ret = ret

    def __str__(self):
        return "@(%s)%s" % (",".join(str(p) for p in self.params), self.ret)


VOID = VoidT()
BOOL = BoolT()
S8 = IntT(8, True)
S16 = IntT(16, True)
S32 = IntT(32, True)
S64 = IntT(64, True)
U8 = IntT(8, False)
U16 = IntT(16, False)
U32 = IntT(32, False)
U64 = IntT(64, False)
F32 = FloatT(32)
F64 = FloatT(64)

PRIMS = {
    "v": VOID, "b": BOOL,
    "s8": S8, "s16": S16, "s32": S32, "s64": S64,
    "u8": U8, "u16": U16, "u32": U32, "u64": U64,
    "f32": F32, "f64": F64,
}


def is_int(t):
    return t.kind == "int"


def is_num(t):
    return t.kind in ("int", "float")
