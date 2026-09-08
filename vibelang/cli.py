"""vibec - the VIBE compiler command line.

  vibec prog.vibe -o prog      compile to a static x86-64 Linux executable
  vibec prog.vibe --run        compile to a temp file and run it
  vibec prog.vibe --ir         print the mid-level IR
  vibec prog.vibe -O0          no optimisation, no register allocation
  vibec --version              print the version

No assembler, linker or C library is involved: vibec writes the ELF bytes.
"""

import os
import subprocess
import sys
import tempfile

from .front import build, CheckError
from .parser import ParseError
from .lexer import LexError
from .codegen import compile_program

VERSION = "0.1.0"

USAGE = __doc__


def stdlib_dir():
    """Where the .vibe standard library lives.

    Checked in order so a checkout, a pip install and a system package all
    work without configuration.
    """
    env = os.environ.get("VIBE_LIB")
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "stdlib"),
                 os.path.join(os.path.dirname(here), "lib"),
                 "/usr/lib/vibe/lib",
                 "/usr/local/lib/vibe/lib"):
        if os.path.isdir(cand):
            return cand
    return here


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    src = None
    out = None
    mode = "build"
    noopt = False
    i = 1
    while i < len(argv):
        x = argv[i]
        if x in ("--version", "-V"):
            print("vibec %s" % VERSION)
            return 0
        if x in ("-h", "--help"):
            sys.stdout.write(USAGE)
            return 0
        if x == "-o":
            i += 1
            if i >= len(argv):
                sys.stderr.write("vibec: -o needs a file name\n")
                return 2
            out = argv[i]
        elif x == "--ir":
            mode = "ir"
        elif x == "--run":
            mode = "run"
        elif x == "-O0":
            noopt = True
        elif x.startswith("-"):
            sys.stderr.write("vibec: unknown option %s\n" % x)
            return 2
        else:
            src = x
        i += 1

    if src is None:
        sys.stderr.write(USAGE)
        return 2
    if not os.path.exists(src):
        sys.stderr.write("vibec: no such file: %s\n" % src)
        return 2

    try:
        prog = build(src, include_dirs=[stdlib_dir()])
    except (LexError, ParseError, CheckError) as e:
        sys.stderr.write("%s\n" % e)
        return 1

    if mode == "ir":
        print(prog.dump())
        return 0

    blob = compile_program(prog, opt=not noopt)

    if mode == "run":
        fd, path = tempfile.mkstemp(prefix="vibe-")
        os.write(fd, blob)
        os.close(fd)
        os.chmod(path, 0o755)
        try:
            r = subprocess.run([path])
        finally:
            os.unlink(path)
        return r.returncode

    if out is None:
        base = os.path.basename(src)
        out = base[:-5] if base.endswith(".vibe") else base + ".out"
    with open(out, "wb") as fh:
        fh.write(blob)
    os.chmod(out, 0o755)
    return 0


if __name__ == "__main__":
    sys.exit(main())
