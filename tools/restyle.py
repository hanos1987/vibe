#!/usr/bin/env python3
"""Rewrite VIBE source in the economical 0.2 style, in place.

  python3 tools/restyle.py file.vibe ...

Changes only what is provably equivalent: outer parentheses a level does
not need, `x = x + 1` to `x += 1`, `$~ i s64 = 0` to `$~ i = 0` (only for
s64 / f64 literals, where inference gives the same type). Recompile and
run your tests afterwards; the tool is conservative but not a compiler.
"""
import re
import sys

BIN = ["<<", ">>", "<=", ">=", "==", "!=", "&&", "||",
       "+", "-", "*", "/", "%", "&", "|", "^", "<", ">"]


def depth0_ops(s):
    """Distinct binary operators at bracket depth 0 of an expression."""
    ops = set()
    d = 0
    i = 0
    instr = None
    while i < len(s):
        c = s[i]
        if instr:
            if c == "\\":
                i += 2
                continue
            if c == instr:
                instr = None
            i += 1
            continue
        if c in "\"":
            instr = c
        elif c == "`":
            i += 2 if s[i + 1:i + 2] != "\\" else 3
            continue
        elif c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        elif d == 0:
            for op in BIN:
                if s.startswith(op, i):
                    # unary minus / not / deref-and-address are not binary
                    prev = s[:i].rstrip()
                    if op in ("-", "&", "*", "!", "~") and (
                            not prev or prev[-1] in "(,=<>!&|+-*/%^["):
                        break
                    ops.add(op)
                    i += len(op) - 1
                    break
        i += 1
    return ops


def balanced(s):
    d = 0
    for c in s:
        if c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
            if d < 0:
                return False
    return d == 0


def strip_outer(expr):
    """`(a + b)` -> `a + b` when the level would not need them."""
    e = expr.strip()
    while e.startswith("(") and e.endswith(")") and balanced(e[1:-1]):
        inner = e[1:-1].strip()
        ops = depth0_ops(inner)
        if len(ops) <= 1:
            e = inner
        else:
            break
    return e


def restyle_line(line):
    m = re.match(r"^(\s*)(.*?)(\s*;.*)?$", line)
    ind, body, comment = m.group(1), m.group(2), m.group(3) or ""
    if not body:
        return line
    # bindings with a redundant type
    b = re.match(r"^(\$~?) (\w+) (s64|f64) = (.+)$", body)
    if b and re.match(r"^-?\d+$" if b.group(3) == "s64" else r"^-?\d+\.\d+$",
                      b.group(4).strip()):
        body = "%s %s = %s" % (b.group(1), b.group(2), b.group(4))
    # x = (x op y) -> x op= y
    a = re.match(r"^([\w.\[\]']+) = \((\S+) ([-+*/%&|^]|<<|>>) (.+)\)$", body)
    if a and a.group(1) == a.group(2) and "(" not in a.group(1):
        rhs = a.group(4)
        if balanced(rhs) and (len(depth0_ops(rhs)) == 0 or
                              (rhs.startswith("(") and rhs.endswith(")"))):
            body = "%s %s= %s" % (a.group(1), a.group(3), strip_outer(rhs))
    # ? (c) {   * (c) {   ^ (e)   x = (e)   ?? (e) {
    for pat in (r"^(\? |\* |\?\? |\^ )\((.*)\)( \{)?$",
                r"^([\w.\[\]']+ = )\((.*)\)$"):
        c = re.match(pat, body)
        if c and balanced(c.group(2)):
            tail = c.group(3) if c.lastindex == 3 and c.group(3) else ""
            body = c.group(1) + strip_outer("(" + c.group(2) + ")") + tail
            break
    return ind + body + comment + ("\n" if line.endswith("\n") else "")


def main(paths):
    for p in paths:
        with open(p) as fh:
            src = fh.readlines()
        out = [restyle_line(l) for l in src]
        with open(p, "w") as fh:
            fh.writelines(out)
        print("restyled", p)


if __name__ == "__main__":
    main(sys.argv[1:])
