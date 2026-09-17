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


def _locals(fn):
    names = set(p for (p, _) in fn.params)
    names.update(fn.tparams or ())

    def walk(n):
        if isinstance(n, (list, tuple)):
            for x in n:
                walk(x)
            return
        if not isinstance(n, A.Node):
            return
        if isinstance(n, (A.Let, A.For)):
            names.add(n.name)
        if isinstance(n, A.PVar):
            names.update(n.binds)
        for f in getattr(n, "__slots__", ()):
            walk(getattr(n, f, None))
    walk(fn.body)
    return names


def prefix(decls, ns, names):
    """Rename every name in `names`, at its declaration and at each use
    inside decls, to ns.name."""
    def q(n):
        return "%s.%s" % (ns, n)

    def walk(n, local):
        if isinstance(n, (list, tuple)):
            for x in n:
                walk(x, local)
            return
        if not isinstance(n, A.Node):
            return
        if isinstance(n, A.TNamed) and n.name in names:
            n.name = q(n.name)
        elif isinstance(n, (A.StructLit, A.SumLit)) and n.tyname in names:
            n.tyname = q(n.tyname)
        elif isinstance(n, (A.Call, A.FnRef, A.Ident)) \
                and n.name in names and n.name not in local:
            n.name = q(n.name)
        for f in getattr(n, "__slots__", ()):
            walk(getattr(n, f, None), local)

    for d in decls:
        local = _locals(d) if isinstance(d, A.FnDecl) else set()
        walk(d, local)
        if getattr(d, "name", None) in names and not isinstance(
                d, (A.TNamed, A.Call, A.FnRef, A.Ident)):
            d.name = q(d.name)
