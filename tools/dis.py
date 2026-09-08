#!/usr/bin/env python3
"""Disassemble the code emitted for one VIBE function.

  python3 tools/dis.py prog.vibe fib

Uses objdump on the raw code bytes; VIBE binaries carry no section headers.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vibelang.front import build                      # noqa: E402
from vibelang.codegen import CodeGen                  # noqa: E402


def main(argv):
    src = argv[1]
    want = argv[2] if len(argv) > 2 else None
    from vibelang.cli import stdlib_dir
    libdir = stdlib_dir()
    prog = build(src, include_dirs=[libdir])
    cg = CodeGen(prog, opt=("-O0" not in argv))
    cg.run()
    code = bytes(cg.asm.buf)
    fnames = set(f.name for f in prog.funcs)
    labels = sorted(((v, k) for k, v in cg.asm.labels.items() if k in fnames))

    if want is None:
        for off, name in labels:
            print("%6d  %s" % (off, name))
        return 0

    start = None
    end = len(code)
    for i, (off, name) in enumerate(labels):
        if name == want:
            start = off
            for off2, _ in labels[i + 1:]:
                if off2 > off:
                    end = off2
                    break
            break
    if start is None:
        print("no such function: %s" % want)
        return 1
    blob = code[start:end]
    fd, path = tempfile.mkstemp()
    os.write(fd, blob)
    os.close(fd)
    try:
        r = subprocess.run(
            ["objdump", "-D", "-b", "binary", "-m", "i386:x86-64",
             "-M", "intel", path], capture_output=True, text=True)
        lines = r.stdout.split("\n")
        started = False
        n = 0
        for l in lines:
            if l.strip().startswith("0:"):
                started = True
            if started and l.strip():
                print(l)
                n += 1
        print("\n%d bytes, %d instructions" % (len(blob), n))
    finally:
        os.unlink(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
