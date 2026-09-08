"""VIBE AST nodes. Deliberately flat and uniform: every node carries `line`
so diagnostics are always precise."""


class Node:
    __slots__ = ("line", "col", "ty", "_file")

    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
        self.ty = None
        self._file = None


def _mk(name, fields):
    """Build a small AST node class with the given extra fields."""
    ns = {"__slots__": tuple(fields), "NAME": name}

    def __init__(self, *args, line=0, col=0):
        Node.__init__(self, line, col)
        assert len(args) == len(fields), (name, len(args), len(fields))
        for f, a in zip(fields, args):
            setattr(self, f, a)

    def __repr__(self):
        return "%s(%s)" % (name, ", ".join(repr(getattr(self, f)) for f in fields))

    ns["__init__"] = __init__
    ns["__repr__"] = __repr__
    return type(name, (Node,), ns)


# ---- type expressions (syntax, resolved later) -----------------------------
TName = _mk("TName", ["name"])            # s64, b, v ...
TPtr = _mk("TPtr", ["to"])
TArr = _mk("TArr", ["n", "elem"])
TNamed = _mk("TNamed", ["name"])          # %Point
TFn = _mk("TFn", ["params", "ret"])       # @(s64, s64) s64

# ---- declarations ----------------------------------------------------------
FnDecl = _mk("FnDecl", ["name", "params", "ret", "body", "entry", "pub"])
StructDecl = _mk("StructDecl", ["name", "fields"])
SumDecl = _mk("SumDecl", ["name", "variants"])
GlobalDecl = _mk("GlobalDecl", ["name", "ty", "init", "mut", "const"])
Include = _mk("Include", ["path"])

# ---- statements ------------------------------------------------------------
Let = _mk("Let", ["name", "ty", "init", "mut"])
Assign = _mk("Assign", ["target", "value"])
Return = _mk("Return", ["value"])
If = _mk("If", ["cond", "then", "els"])
While = _mk("While", ["cond", "body"])
Break = _mk("Break", [])
Continue = _mk("Continue", [])
Match = _mk("Match", ["subject", "arms"])   # arms: [(Pattern, [stmt])]
ExprStmt = _mk("ExprStmt", ["expr"])
AsmBytes = _mk("AsmBytes", ["values"])

# ---- patterns --------------------------------------------------------------
PVar = _mk("PVar", ["variant", "binds"])    # |Var(a, b)
PWild = _mk("PWild", [])                    # |_

# ---- expressions -----------------------------------------------------------
IntLit = _mk("IntLit", ["v"])
FltLit = _mk("FltLit", ["v"])
StrLit = _mk("StrLit", ["v"])
Ident = _mk("Ident", ["name"])
Bin = _mk("Bin", ["op", "a", "b"])
Un = _mk("Un", ["op", "a"])
Call = _mk("Call", ["name", "args"])
CallP = _mk("CallP", ["callee", "args"])
FnRef = _mk("FnRef", ["name"])            # @name  -- address of a function
Syscall = _mk("Syscall", ["num", "args"])
Index = _mk("Index", ["base", "idx"])
Field = _mk("Field", ["base", "name"])
Deref = _mk("Deref", ["p"])
Addr = _mk("Addr", ["e"])
Cast = _mk("Cast", ["ty", "e"])
SizeOf = _mk("SizeOf", ["ty"])
StructLit = _mk("StructLit", ["tyname", "inits"])
ArrLit = _mk("ArrLit", ["items"])
SumLit = _mk("SumLit", ["tyname", "variant", "args"])
