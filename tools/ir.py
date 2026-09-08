#!/usr/bin/env python3
"""Dump the IR of one function after optimisation.

  python3 tools/ir.py prog.vibe px [--raw]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vibelang.front import build          # noqa: E402
from vibelang.opt import optimise         # noqa: E402


def main(argv):
    src = argv[1]
    want = argv[2] if len(argv) > 2 else None
    from vibelang.cli import stdlib_dir
    libdir = stdlib_dir()
    prog = build(src, include_dirs=[libdir])
    if "--raw" not in argv:
        optimise(prog)
    for f in prog.funcs:
        if want and f.name != want:
            continue
        print(f.dump())
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
