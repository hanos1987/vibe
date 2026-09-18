"""vibec - the VIBE compiler command line.

  vibec prog.vibe -o prog      compile to a static x86-64 Linux executable
  vibec prog.vibe --run        compile to a temp file and run it
  vibec prog.vibe --ir         print the mid-level IR
  vibec prog.vibe -O0          no optimisation, no register allocation
  vibec prog.vibe --backend c  build through gcc/clang -O3 (fastest code)
  vibec prog.vibe --emit-c     print the generated C
  vibec prog.vibe -s           strip the symbol table from the binary
  vibec prog.vibe --check      trap, with file:line, on a bad index or divide by zero
  vibec prog.vibe --json       report errors as JSON on stdout
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

VERSION = "0.2.0"

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
    backend = "native"
    explicit_backend = False
    as_json = False
    check = False
    strip = False
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
        elif x == "--backend" or x.startswith("--backend="):
            explicit_backend = True
            if "=" in x:
                backend = x.split("=", 1)[1]
            else:
                i += 1
                backend = argv[i] if i < len(argv) else ""
            if backend not in ("native", "c"):
                sys.stderr.write("vibec: --backend is native or c\n")
                return 2
        elif x in ("-s", "--strip"):
            strip = True
        elif x == "--check":
            check = True
        elif x == "--json":
            as_json = True
        elif x == "--emit-c":
            mode = "c"
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
        prog = build(src, include_dirs=[stdlib_dir()], check=check)
    except (LexError, ParseError, CheckError) as e:
        if as_json:
            import json
            import re
            out = []
            for line in str(e).split("\n"):
                m = re.match(r"(.*?):(\d+):(\d+): (.*)", line)
                if m:
                    out.append({"file": m.group(1), "line": int(m.group(2)),
                                "col": int(m.group(3)), "message": m.group(4)})
                elif line:
                    out.append({"message": line})
            sys.stdout.write(json.dumps(out) + "\n")
        else:
            sys.stderr.write("%s\n" % e)
        return 1

    if mode == "ir":
        print(prog.dump())
        return 0

    if mode == "c":
        from .cback import emit_c
        sys.stdout.write(emit_c(prog))
        return 0

    if prog.externs and backend == "native":
        if explicit_backend:
            sys.stderr.write("vibec: this program declares C functions (@<); "
                             "build it with --backend=c\n")
            return 1
        backend = "c"

    if backend == "c":
        from .cback import compile_program_c
        try:
            blob = compile_program_c(prog)
        except RuntimeError as e:
            sys.stderr.write("vibec: %s\n" % e)
            return 1
    else:
        blob = compile_program(prog, opt=not noopt, strip=strip)

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
