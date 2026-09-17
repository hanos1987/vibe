"""Namespaced includes:  <<"geom.vibe" g   makes every top-level name of that
file (and of the files it includes) available as g.name, and only as that.

Done as a rewrite of the included files' syntax trees before checking, so
the rest of the compiler sees ordinary, already-unique names.
"""

from . import ast_ as A


def declared(decls):
    out = set()
    for d in decls:
        if isinstance(d, (A.FnDecl, A.StructDecl, A.SumDecl, A.GlobalDecl)):
            if d.name != "@!":
                out.add(d.name)
    return out


def prefix(decls, ns, names):
    """Rename every name in `names`, at its declaration and at each use
    inside decls, to ns.name."""
    def q(n):
        return "%s.%s" % (ns, n)

    def rename(n, local):
        if isinstance(n, A.TNamed) and n.name in names:
            n.name = q(n.name)
        elif isinstance(n, (A.StructLit, A.SumLit)) and n.tyname in names:
            n.tyname = q(n.tyname)
        elif isinstance(n, (A.Call, A.FnRef, A.Ident)) \
                and n.name in names and n.name not in local:
            n.name = q(n.name)

    def walk(n, local):
        """Expressions and types: rename under the locals in force."""
        if isinstance(n, (list, tuple)):
            for x in n:
                walk(x, local)
            return
        if not isinstance(n, A.Node):
            return
        rename(n, local)
        for f in getattr(n, "__slots__", ()):
            walk(getattr(n, f, None), local)

    def block(stmts, local):
        """Statements in order: a binding hides a file-level name only from
        the statements after it, and only inside its own block."""
        local = set(local)
        for st in stmts:
            if isinstance(st, A.Let):
                walk(st.ty, local)
                walk(st.init, local)
                local.add(st.name)
            elif isinstance(st, A.For):
                walk(st.lo, local)
                walk(st.hi, local)
                block(st.body, local | {st.name})
            elif isinstance(st, A.If):
                walk(st.cond, local)
                block(st.then, local)
                if st.els is not None:
                    block(st.els if isinstance(st.els, list) else [st.els],
                          local)
            elif isinstance(st, A.While):
                walk(st.cond, local)
                block(st.body, local)
            elif isinstance(st, A.Match):
                walk(st.subject, local)
                for (pat, body) in st.arms:
                    binds = set(pat.binds) if isinstance(pat, A.PVar) else set()
                    block(body, local | binds)
            elif isinstance(st, A.Defer):
                block([st.stmt], local)
            else:
                walk(st, local)

    for d in decls:
        if isinstance(d, A.FnDecl):
            local = set(p for (p, _) in d.params) | set(d.tparams or ())
            for (_, pt) in d.params:
                walk(pt, local)
            walk(d.ret, local)
            block(d.body, local)
        else:
            walk(d, set())
        if getattr(d, "name", None) in names and not isinstance(
                d, (A.TNamed, A.Call, A.FnRef, A.Ident)):
            d.name = q(d.name)
