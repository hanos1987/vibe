#!/usr/bin/env python3
"""Benchmark VIBE against gcc on identical programs.

Reports best-of-N wall clock and verifies every build prints the same answer,
so a fast-but-wrong result cannot pass unnoticed.
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VIBEC = os.path.join(ROOT, "vibec")
BENCHES = ["fib", "sieve", "matmul", "mandel"]
REPS = 3


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("failed: %s\n%s" % (" ".join(cmd), r.stderr))
    return r


def timeit(path):
    best = None
    out = None
    for _ in range(REPS):
        t0 = time.perf_counter()
        r = subprocess.run([path], capture_output=True, text=True)
        dt = time.perf_counter() - t0
        if r.returncode != 0:
            raise SystemExit("%s exited %d" % (path, r.returncode))
        out = r.stdout.strip()
        if best is None or dt < best:
            best = dt
    return best, out


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "_mkc.py")], check=True)
    rows = []
    for name in BENCHES:
        v = os.path.join(HERE, name + ".vibe")
        c = os.path.join(HERE, name + ".c")
        bv = os.path.join(HERE, name + ".vibe.bin")
        b0 = os.path.join(HERE, name + ".c0.bin")
        b2 = os.path.join(HERE, name + ".c2.bin")

        sh([sys.executable, VIBEC, v, "-o", bv])
        sh(["gcc", "-O0", "-o", b0, c])
        sh(["gcc", "-O2", "-o", b2, c])

        tv, ov = timeit(bv)
        t0, o0 = timeit(b0)
        t2, o2 = timeit(b2)
        agree = (ov == o0 == o2)
        rows.append((name, tv, t0, t2, agree, ov))

    w = max(len(r[0]) for r in rows) + 2
    print()
    print("%-*s %10s %10s %10s   %8s %8s  %s" %
          (w, "bench", "VIBE", "gcc -O0", "gcc -O2",
           "vs -O0", "vs -O2", "result"))
    print("-" * (w + 62))
    for (name, tv, t0, t2, agree, ov) in rows:
        print("%-*s %9.3fs %9.3fs %9.3fs   %7.2fx %7.2fx  %s" %
              (w, name, tv, t0, t2, t0 / tv, t2 / tv,
               ov if agree else "MISMATCH " + ov))
    print("\n(>1.00x means VIBE is faster; all outputs verified identical"
          " unless marked MISMATCH)")


if __name__ == "__main__":
    main()
