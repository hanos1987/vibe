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
COMPOUND = {"+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}
PRIM_NAMES = {"s8", "s16", "s32", "s64", "u8", "u16", "u32", "u64",
              "f32", "f64", "b", "v",
              "f32x4", "f32x8", "f64x2", "f64x4", "s32x4", "s32x8"}


def has_call(e):
    if isinstance(e, (A.Call, A.CallP, A.Syscall, A.Intrinsic)):
        return True
    for f in getattr(e, "__slots__", ()):
        x = getattr(e, f)
        if isinstance(x, A.Node) and has_call(x):
            return True
    return False


CHAINABLE = {"+", "*", "&", "|", "^", "&&", "||"}

# (PRIM_NAMES is defined once, above)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, src, filename="<vibe>", generics=()):
        self.file = filename
        self.toks = lex(src, filename)
        self.i = 0
        self.generics = set(generics)   # names declared as @ name<...>
        self.split = []         # `>>` tokens narrowed to `>` by parse_targs

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
            ns = self.next().val if self.t.kind == "ID" else None
            self.end_stmt()
            return A.Include(p, ns, line=t.line, col=t.col)
        if self.at("@<"):
            return self.parse_extern()
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
    def parse_extern(self):
        """@< "lib" name (T, ...) R   -- a C function from a library"""
        t = self.next()
        if self.t.kind != "STR":
            self.err("expected the library name, e.g. @< \"c\" puts (*u8) s32")
        lib = self.next().val.decode("utf-8")
        name = self.expect_id("function name")
        csym = name
        if self.eat("="):
            # @< "c" cabs = abs (s32) s32 : VIBE name, then the C symbol
            csym = self.expect_id("C symbol name")
        self.expect("(", "to open the parameter list")
        params = []
        variadic = False
        while not self.at(")"):
            if self.eat("..."):
                variadic = True
                break
            # a parameter name is optional and ignored
            if self.t.kind == "ID" and self.t.val not in PRIM_NAMES:
                self.next()
            params.append(self.parse_type())
            if not self.eat(","):
                break
        self.expect(")", "to close the parameter list")
        ret = self.parse_type()
        self.end_stmt()
        return A.ExternDecl(lib, name, params, ret, variadic, csym,
                            line=t.line, col=t.col)

    def parse_fn(self):
        t = self.next()
        entry = (t.val == "@!")
        name = "@!" if entry else self.expect_id("function name")
        tparams = None if entry else self.parse_tparams()
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
        return A.FnDecl(name, params, ret, body, entry, True, tparams,
                        line=t.line, col=t.col)

    def parse_struct(self):
        t = self.expect("%")
        name = self.expect_id("struct name")
        tparams = self.parse_tparams()
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
        return A.StructDecl(name, fields, tparams, line=t.line, col=t.col)

    def parse_sum(self):
        t = self.expect("%|")
        name = self.expect_id("sum type name")
        tparams = self.parse_tparams()
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
        return A.SumDecl(name, variants, tparams, line=t.line, col=t.col)

    def parse_global(self):
        t = self.next()
        const = (t.val == "$$")
        mut = (t.val == "$~")
        name = self.expect_id("name")
        ty = None
        if not self.at("="):
            ty = self.parse_type()
        init = None
        if self.eat("="):
            init = self.parse_expr()
        elif ty is None:
            self.err("a global needs a type, a value, or both")
        self.end_stmt()
        if ty is None:
            # `$~ total = 0`: an integer literal is s64, a float f64
            lit = init.a if isinstance(init, A.Un) else init
            if isinstance(lit, A.FltLit):
                ty = A.TName("f64", line=t.line, col=t.col)
            elif isinstance(lit, A.IntLit):
                ty = A.TName("s64", line=t.line, col=t.col)
            else:
                self.err("a global initialised with an expression needs "
                         "its type written out")
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
            name = self.dotted("type name")
            return A.TNamed(name, self.parse_targs(), line=t.line, col=t.col)
        if t.kind == "ID":
            self.next()
            return A.TName(t.val, line=t.line, col=t.col)
        self.err("expected a type")

    def dotted(self, what):
        """name or ns.name"""
        name = self.expect_id(what)
        if self.at(".") and self.peek().kind == "ID":
            self.next()
            name = "%s.%s" % (name, self.next().val)
        return name

    def parse_tparams(self):
        """<T, U> after a declared name, or None."""
        if not self.at("<"):
            return None
        self.next()
        out = []
        while True:
            out.append(self.expect_id("type parameter name"))
            if not self.eat(","):
                break
        self.expect(">", "to close the type parameter list")
        return out

    def parse_targs(self):
        """<type, ...> after a generic name, or None. A closing `>>` is
        split, so %Vec<%Vec<s64>> needs no space."""
        if not self.at("<"):
            return None
        self.next()
        out = []
        while True:
            out.append(self.parse_type())
            if not self.eat(","):
                break
        if self.at(">>"):
            self.split.append(self.t)
            self.t.val = ">"
        else:
            self.expect(">", "to close the type argument list")
        return out

    def try_call_targs(self):
        """At `<` after a name: `name<types>(` is a generic call. Anything
        else is a comparison, and the parser is left where it was."""
        save = self.i
        nsplit = len(self.split)
        try:
            targs = self.parse_targs()
            if self.at("("):
                self.last_targs = targs
                return targs
        except ParseError:
            pass
        for tok in self.split[nsplit:]:
            tok.val = ">>"
        del self.split[nsplit:]
        self.i = save
        return None

    def star_is_cast(self):
        """At a statement-leading `*`: is this `*T(expr)...`, a pointer cast,
        rather than a loop? True when a primitive or sigil type follows and
        is itself followed by `(`."""
        # a store has an assignment on its line, outside any brackets,
        # before any block opens; `* s64(x) < 3 {` is a loop
        depth = 0
        j = 1
        while True:
            tk = self.peek(j)
            if tk.kind in ("NL", "EOF"):
                return False
            if tk.kind == "P":
                if tk.val in ("(", "["):
                    depth += 1
                elif tk.val in (")", "]"):
                    depth -= 1
                elif depth == 0 and tk.val == "{":
                    return False
                elif depth == 0 and (tk.val == "=" or tk.val in COMPOUND):
                    break
            j += 1
        k = 1
        while self.peek(k).is_p("*"):
            k += 1
        a, b = self.peek(k), self.peek(k + 1)
        if a.is_p("%"):
            a, b = self.peek(k + 1), self.peek(k + 2)
            return a.kind == "ID" and b.is_p("(")
        return (a.kind == "ID" and a.val in PRIM_NAMES and a.val != "b"
                and b.is_p("("))

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

        if self.at("~"):
            # a statement cannot begin with bitwise-not, so this is defer
            self.next()
            if self.at("~", "$", "$~", "^", "*<", "*>"):
                self.err("~ defers a call or an assignment")
            inner = self.parse_stmt()
            return A.Defer(inner, line=t.line, col=t.col)

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
            # the else may sit on the line after the closing brace
            k = 0
            while self.peek(k).kind == "NL":
                k += 1
            if k and self.peek(k).is_p(":"):
                self.skip_nl()
            if self.at(":"):
                self.next()
                if self.at("?"):
                    els = [self.parse_stmt()]
                    return A.If(cond, then, els, line=t.line, col=t.col)
                els = self.parse_block()
            self.end_stmt()
            return A.If(cond, then, els, line=t.line, col=t.col)

        if self.at("*") and self.star_is_cast():
            pass        # `*T(p)' = x`: an expression statement, below
        elif self.at("*"):
            self.next()
            nx = self.peek(1)
            neg = (nx.is_p("-") and self.peek(2).kind == "INT"
                   and (self.peek(3).kind in ("ID", "INT")
                        or self.peek(3).is_p("(", "-")))
            if self.t.kind == "ID" and (nx.kind in ("ID", "INT") or neg):
                # counted loop: * i lo hi { }   (hi is exclusive)
                name = self.next().val
                # the start is a bare name or number, never `a(...)`: the
                # bound may begin with a parenthesis
                if neg:
                    self.next()
                lt = self.next()
                lo = (A.IntLit(-lt.val if neg else lt.val,
                               line=lt.line, col=lt.col)
                      if lt.kind == "INT"
                      else A.Ident(lt.val, line=lt.line, col=lt.col))
                hi = self.parse_unary()
                body = self.parse_block()
                self.end_stmt()
                return A.For(name, lo, hi, body, line=t.line, col=t.col)
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
        if self.t.kind == "P" and self.t.val in COMPOUND:
            op = self.next().val[:-1]
            val = self.parse_expr()
            self.end_stmt()
            if has_call(e):
                self.err("the target of %s= is evaluated twice, so it may "
                         "not contain a call" % op, t)
            val = A.Bin(op, e, val, line=t.line, col=t.col)
            return A.Assign(e, val, line=t.line, col=t.col)
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
            elif self.at("!"):
                # postfix: unwrap, or return the failure to the caller (a
                # prefix ! can never follow a complete operand)
                self.next()
                e = A.Try(e, line=t.line, col=t.col)
            elif self.at("."):
                self.next()
                e = A.Field(e, self.expect_id("field name"),
                            line=t.line, col=t.col)
            elif self.at("["):
                self.next()
                idx = self.parse_expr()
                self.expect("]")
                e = A.Index(e, idx, line=t.line, col=t.col)
            elif self.at("<") and isinstance(e, A.Ident) \
                    and e.name in self.generics \
                    and self.try_call_targs() is not None:
                targs = self.last_targs
                self.next()
                args = self.parse_args()
                e = A.Call(e.name, args, targs, line=t.line, col=t.col)
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
            if self.t.kind == "ID":
                name = self.next().val
                self.expect("(", "to open the intrinsic argument list")
                args = self.parse_args()
                return A.Intrinsic(name, args, line=t.line, col=t.col)
            if self.t.kind != "INT":
                self.err("\\ takes a syscall number or an intrinsic name, "
                         "e.g. \\1(...) or \\sqrt(x)")
            num = self.next().val
            self.expect("(", "to open the syscall argument list")
            args = self.parse_args()
            return A.Syscall(num, args, line=t.line, col=t.col)
        if self.at("@"):
            self.next()
            return A.FnRef(self.dotted("function name"),
                           line=t.line, col=t.col)
        if self.at("%"):
            self.next()
            name = self.dotted("type name")
            targs = self.parse_targs()
            if self.at("|"):
                self.next()
                vn = self.expect_id("variant name")
                args = []
                if self.eat("("):
                    args = self.parse_args()
                return A.SumLit(name, vn, args, targs, line=t.line, col=t.col)
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
            return A.StructLit(name, inits, targs, line=t.line, col=t.col)
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


def parse(src, filename="<vibe>", generics=()):
    return Parser(src, filename, generics).parse_unit()
