#!/usr/bin/env python3
"""Token cost of VIBE against C for the benchmark pairs (needs tiktoken).

  python3 tools/tokens.py            # bench/*.vibe vs bench/*.c (run bench first)
  python3 tools/tokens.py a.vibe:a.c ...
"""
import glob
import os
import re
import sys

try:
    import tiktoken
except ImportError:
    sys.exit("pip install tiktoken")

enc = tiktoken.get_encoding("o200k_base")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip(src, lang):
    out = []
    if lang == "c":
        src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    for line in src.split("\n"):
        if lang == "vibe":
            if '"' not in line:
                line = re.sub(r"\s*;.*$", "", line)
        else:
            line = re.sub(r"\s*//.*$", "", line)
        if line.strip():
            out.append(line.rstrip())
    return "\n".join(out)


pairs = sys.argv[1:] or [
    "%s:%s" % (v, v[:-5] + ".c")
    for v in sorted(glob.glob(os.path.join(HERE, "bench", "*.vibe")))
    if os.path.exists(v[:-5] + ".c")]
tv = tc = 0
for pair in pairs:
    v, c = pair.split(":")
    a = len(enc.encode(strip(open(v).read(), "vibe")))
    b = len(enc.encode(strip(open(c).read(), "c")))
    tv += a
    tc += b
    print("%-24s VIBE %5d   C %5d   %.2fx" % (os.path.basename(v), a, b, a / b))
if tc:
    print("%-24s VIBE %5d   C %5d   %.2fx" % ("total", tv, tc, tv / tc))
