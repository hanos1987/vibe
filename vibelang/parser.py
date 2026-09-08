"""VIBE parser.

Grammar is fully sigil-driven and locally decidable: the first token of any
declaration or statement determines its form, with no lookahead beyond one
token except for the assignment/expression-statement split.

Operators have NO precedence. `(a + b * c)` is a compile error; write
`(a + (b * c))`. Chains of one associative operator are allowed
(`(a + b + c)`); mixing distinct operators without parentheses is rejected.
Comparison operators never chain.
"""

from .lexer import lex, Tok
from . import ast_ as A

BIN_OPS = {
    "+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>",
    "==", "!=", "<", ">", "<=", ">=", "&&", "||",
}
CMP_OPS = {"==", "!=", "<", ">", "<=", ">="}
# Operators that may repeat in an unparenthesised chain.
CHAINABLE = {"+", "-", "*", "/", "%", "&", "|", "^", "&&", "||"}

PRIM_NAMES = {"v", "b", "s8", "s16", "s32", "s64",
              "u8", "u16", "u32", "u64", "f32", "f64"}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, src, filename="<vibe>"):
        self.file = filename
        self.toks = lex(src, filename)
        self.i = 0

    # -- token helpers -------------------------------------------------------
    @property
    def t(self):
        return self.toks[self.i]

    def peek(self, k=1):
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else self.toks[-1]

    def next(self):
        t = self.toks[self.i]
        if t.kind != "EOF":
            self.i += 1
        return t

    def err(self, msg, tok=None):
        tok = tok or self.t
        raise ParseError("%s:%d:%d: %s (at %s)" %
                         (self.file, tok.line, tok.col, msg,
                          tok.val if tok.kind != "EOF" else "end of file"))

    def at(self, *vals):
        return self.t.kind == "P" and self.t.val in vals

    def eat(self, val):
        if self.at(val):
            self.next()
            return True
        return False

    def expect(self, val, what=None):
        if not self.at(val):
            self.err("expected '%s'%s" % (val, (" " + what) if what else ""))
        return self.next()

    def expect_id(self, what="identifier"):
        if self.t.kind != "ID":
            self.err("expected " + what)
        return self.next().val

    def skip_nl(self):
        while self.t.kind == "NL":
            self.next()

    def end_stmt(self):
        if self.t.kind == "NL":
            self.next()
            return
        if self.at("}") or self.t.kind == "EOF":
            return
        self.err("expected end of line")

    # -- entry ---------------------------------------------------------------
    def parse_unit(self):
        decls = []
        self.skip_nl()
        while self.t.kind != "EOF":
            decls.append(self.parse_decl())
            self.skip_nl()
        return decls

    def parse_decl(self):
        t = self.t
        if self.at("<<"):
            self.next()
            if self.t.kind != "STR":
                self.err("expected \"path\" after <<")
            p = self.next().val.decode("utf-8")
            self.end_stmt()
            return A.Include(p, line=t.line, col=t.col)
        if self.at("@", "@!"):
            return self.parse_fn()
        if self.at("%|"):
            return self.parse_sum()
        if self.at("%"):
            return self.parse_struct()
        if self.at("$", "$~", "$$"):
            return self.parse_global()
        self.err("expected a declaration sigil (@ %% $ <<)")

    # -- declarations --------------------------------------------------------
    def parse_fn(self):
        t = self.next()
        entry = (t.val == "@!")
        name = "@!" if entry else self.expect_id("function name")
        self.expect("(", "to open the parameter list")
        params = []
        if not self.at(")"):
            while True:
                pn = self.expect_id("parameter name")
                pt = self.parse_type()
                params.append((pn, pt))
                if not self.eat(","):
                    break
        self.expect(")", "to close the parameter list")
        ret = self.parse_type()
        body = self.parse_block()
        self.end_stmt()
        return A.FnDecl(name, params, ret, body, entry, True,
                        line=t.line, col=t.col)

    def parse_struct(self):
        t = self.expect("%")
        name = self.expect_id("struct name")
        self.expect("{", "to open the struct body")
        self.skip_nl()
        fields = []
        while not self.at("}"):
            fn = self.expect_id("field name")
            ft = self.parse_type()
            fields.append((fn, ft))
            self.eat(",")
            self.skip_nl()
        self.expect("}")
        self.end_stmt()
        return A.StructDecl(name, fields, line=t.line, col=t.col)

    def parse_sum(self):
        t = self.expect("%|")
        name = self.expect_id("sum type name")
        self.expect("{", "to open the sum body")
        self.skip_nl()
        variants = []
        while not self.at("}"):
            self.expect("|", "before a variant name")
            vn = self.expect_id("variant name")
            vts = []
            if self.eat("("):
                if not self.at(")"):
                    while True:
                        vts.append(self.parse_type())
                        if not self.eat(","):
                            break
                self.expect(")")
            variants.append((vn, vts))
            self.eat(",")
            self.skip_nl()
        self.expect("}")
        self.end_stmt()
        return A.SumDecl(name, variants, line=t.line, col=t.col)

    def parse_global(self):
        t = self.next()
        const = (t.val == "$$")
        mut = (t.val == "$~")
        name = self.expect_id("name")
        ty = self.parse_type()
        init = None
        if self.eat("="):
            init = self.parse_expr()
        self.end_stmt()
        return A.GlobalDecl(name, ty, init, mut, const, line=t.line, col=t.col)

    # -- types ---------------------------------------------------------------
    def parse_type(self):
        t = self.t
        if self.at("@"):
            self.next()
            self.expect("(", "to open a function type")
            ps = []
            if not self.at(")"):
                while True:
                    ps.append(self.parse_type())
                    if not self.eat(","):
                        break
            self.expect(")")
            return A.TFn(ps, self.parse_type(), line=t.line, col=t.col)
        if self.at("*"):
            self.next()
            return A.TPtr(self.parse_type(), line=t.line, col=t.col)
        if self.at("["):
            self.next()
            if self.t.kind == "INT":
                n = self.next().val
            elif self.t.kind == "ID":
                n = self.next().val          # a $$ constant, resolved later
            else:
                self.err("array length must be an integer or a $$ constant")
            self.expect("]")
            return A.TArr(n, self.parse_type(), line=t.line, col=t.col)
        if self.at("%"):
            self.next()
            return A.TNamed(self.expect_id("type name"), line=t.line, col=t.col)
        if t.kind == "ID":
            self.next()
            return A.TName(t.val, line=t.line, col=t.col)
        self.err("expected a type")

    def at_type_start(self):
        t = self.t
        if t.kind == "ID":
            return True
        return self.at("*", "[", "%", "@")

    # -- blocks and statements ----------------------------------------------
    def parse_block(self):
        self.expect("{", "to open a block")
        self.skip_nl()
        stmts = []
        while not self.at("}"):
            if self.t.kind == "EOF":
                self.err("unterminated block")
            stmts.append(self.parse_stmt())
            self.skip_nl()
        self.expect("}")
        return stmts

    def parse_stmt(self):
        t = self.t
        if self.at("$", "$~"):
            self.next()
            mut = (t.val == "$~")
            name = self.expect_id("name")
            ty = None
            init = None
            if not self.at("="):
                ty = self.parse_type()
            if self.eat("="):
                init = self.parse_expr()
            elif ty is None:
                self.err("a binding needs a type, a value, or both")
            self.end_stmt()
            return A.Let(name, ty, init, mut, line=t.line, col=t.col)

        if self.at("^"):
            self.next()
            val = None
            if self.t.kind != "NL" and not self.at("}"):
                val = self.parse_expr()
            self.end_stmt()
            return A.Return(val, line=t.line, col=t.col)

        if self.at("?"):
            self.next()
            cond = self.parse_expr()
            then = self.parse_block()
            els = None
            if self.at(":"):
                self.next()
                if self.at("?"):
                    els = [self.parse_stmt()]
                    return A.If(cond, then, els, line=t.line, col=t.col)
                els = self.parse_block()
            self.end_stmt()
            return A.If(cond, then, els, line=t.line, col=t.col)

        if self.at("*"):
            self.next()
            cond = self.parse_expr()
            body = self.parse_block()
            self.end_stmt()
            return A.While(cond, body, line=t.line, col=t.col)

        if self.at("*<"):
            self.next()
            self.end_stmt()
            return A.Break(line=t.line, col=t.col)

        if self.at("*>"):
            self.next()
            self.end_stmt()
            return A.Continue(line=t.line, col=t.col)

        if self.at("??"):
            self.next()
            subj = self.parse_expr()
            self.expect("{", "to open the match body")
            self.skip_nl()
            arms = []
            while not self.at("}"):
                self.expect("|", "before a match arm")
                if self.at("_") or (self.t.kind == "ID" and self.t.val == "_"):
                    self.next()
                    pat = A.PWild(line=t.line, col=t.col)
                else:
                    vn = self.expect_id("variant name")
                    binds = []
                    if self.eat("("):
                        if not self.at(")"):
                            while True:
                                binds.append(self.expect_id("binding name"))
                                if not self.eat(","):
                                    break
                        self.expect(")")
                    pat = A.PVar(vn, binds, line=t.line, col=t.col)
                body = self.parse_block()
                arms.append((pat, body))
                self.skip_nl()
            self.expect("}")
            self.end_stmt()
            return A.Match(subj, arms, line=t.line, col=t.col)

        if self.at("\\\\"):
            self.next()
            self.expect("[", "to open an inline byte block")
            vals = []
            while not self.at("]"):
                if self.t.kind != "INT":
                    self.err("inline machine code takes integer byte values")
                v = self.next().val
                if not (0 <= v <= 255):
                    self.err("byte value out of range")
                vals.append(v)
                if not self.eat(","):
                    break
            self.expect("]")
            self.end_stmt()
            return A.AsmBytes(vals, line=t.line, col=t.col)

        # expression statement or assignment
        e = self.parse_expr()
        if self.at("="):
            self.next()
            val = self.parse_expr()
            self.end_stmt()
            return A.Assign(e, val, line=t.line, col=t.col)
        self.end_stmt()
        return A.ExprStmt(e, line=t.line, col=t.col)

    # -- expressions ---------------------------------------------------------
    def parse_expr(self):
        """No precedence: one operator per parenthesised level."""
        first = self.parse_unary()
        if not (self.t.kind == "P" and self.t.val in BIN_OPS):
            return first
        op_tok = self.t
        op = op_tok.val
        self.next()
        rhs = self.parse_unary()
        node = A.Bin(op, first, rhs, line=op_tok.line, col=op_tok.col)
        while self.t.kind == "P" and self.t.val in BIN_OPS:
            nt = self.t
            if nt.val != op:
                self.err(
                    "mixed operators '%s' and '%s' need parentheses; VIBE has "
                    "no operator precedence" % (op, nt.val), nt)
            if op in CMP_OPS or op not in CHAINABLE:
                self.err("operator '%s' does not chain; use parentheses" % op, nt)
            self.next()
            rhs = self.parse_unary()
            node = A.Bin(op, node, rhs, line=nt.line, col=nt.col)
        if op in CMP_OPS:
            pass
        return node

    def parse_unary(self):
        t = self.t
        if self.at("-"):
            self.next()
            return A.Un("-", self.parse_unary(), line=t.line, col=t.col)
        if self.at("!"):
            self.next()
            return A.Un("!", self.parse_unary(), line=t.line, col=t.col)
        if self.at("~"):
            self.next()
            return A.Un("~", self.parse_unary(), line=t.line, col=t.col)
        if self.at("&"):
            self.next()
            return A.Addr(self.parse_unary(), line=t.line, col=t.col)
        if self.at("#"):
            self.next()
            return A.SizeOf(self.parse_type(), line=t.line, col=t.col)
        return self.parse_postfix()

    def parse_postfix(self):
        e = self.parse_primary()
        while True:
            t = self.t
            if self.at("'"):
                self.next()
                e = A.Deref(e, line=t.line, col=t.col)
            elif self.at("."):
                self.next()
                e = A.Field(e, self.expect_id("field name"),
                            line=t.line, col=t.col)
            elif self.at("["):
                self.next()
                idx = self.parse_expr()
                self.expect("]")
                e = A.Index(e, idx, line=t.line, col=t.col)
            elif self.at("("):
                self.next()
                args = self.parse_args()
                if isinstance(e, A.Ident):
                    e = A.Call(e.name, args, line=t.line, col=t.col)
                else:
                    e = A.CallP(e, args, line=t.line, col=t.col)
            else:
                return e

    def parse_args(self):
        args = []
        if not self.at(")"):
            while True:
                args.append(self.parse_expr())
                if not self.eat(","):
                    break
        self.expect(")", "to close the argument list")
        return args

    def parse_primary(self):
        t = self.t
        if t.kind == "INT":
            self.next()
            return A.IntLit(t.val, line=t.line, col=t.col)
        if t.kind == "FLT":
            self.next()
            return A.FltLit(t.val, line=t.line, col=t.col)
        if t.kind == "STR":
            self.next()
            return A.StrLit(t.val, line=t.line, col=t.col)
        if self.at("("):
            self.next()
            e = self.parse_expr()
            self.expect(")")
            return e
        if self.at("*"):
            # pointer cast: *u8(p)
            ty = self.parse_type()
            self.expect("(", "to open a cast")
            e = self.parse_expr()
            self.expect(")")
            return A.Cast(ty, e, line=t.line, col=t.col)
        if self.at("["):
            self.next()
            items = []
            self.skip_nl()
            while not self.at("]"):
                items.append(self.parse_expr())
                self.eat(",")
                self.skip_nl()
            self.expect("]")
            return A.ArrLit(items, line=t.line, col=t.col)
        if self.at("\\"):
            self.next()
            if self.t.kind != "INT":
                self.err("syscall needs a numeric selector, e.g. \\1(...)")
            num = self.next().val
            self.expect("(", "to open the syscall argument list")
            args = self.parse_args()
            return A.Syscall(num, args, line=t.line, col=t.col)
        if self.at("@"):
            self.next()
            return A.FnRef(self.expect_id("function name"),
                           line=t.line, col=t.col)
        if self.at("%"):
            self.next()
            name = self.expect_id("type name")
            if self.at("|"):
                self.next()
                vn = self.expect_id("variant name")
                args = []
                if self.eat("("):
                    args = self.parse_args()
                return A.SumLit(name, vn, args, line=t.line, col=t.col)
            self.expect("{", "to open a struct literal")
            self.skip_nl()
            inits = []
            while not self.at("}"):
                fn = self.expect_id("field name")
                self.expect(":", "after a field name")
                inits.append((fn, self.parse_expr()))
                self.eat(",")
                self.skip_nl()
            self.expect("}")
            return A.StructLit(name, inits, line=t.line, col=t.col)
        if t.kind == "ID":
            # a cast is a primitive type name applied like a call: s64(x)
            if t.val in PRIM_NAMES and self.peek().is_p("("):
                self.next()
                self.next()
                e = self.parse_expr()
                self.expect(")")
                return A.Cast(A.TName(t.val, line=t.line, col=t.col), e,
                              line=t.line, col=t.col)
            self.next()
            return A.Ident(t.val, line=t.line, col=t.col)
        self.err("expected an expression")


def parse(src, filename="<vibe>"):
    return Parser(src, filename).parse_unit()
