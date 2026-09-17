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
    cols = ["VIBE", "VIBE -c", "gcc -O0", "gcc -O2", "gcc -O3"]
    rows = []
    for name in BENCHES:
        v = os.path.join(HERE, name + ".vibe")
        c = os.path.join(HERE, name + ".c")
        bins = [os.path.join(HERE, "%s.%d.bin" % (name, k)) for k in range(5)]
        sh([sys.executable, VIBEC, v, "-o", bins[0]])
        sh([sys.executable, VIBEC, v, "--backend=c", "-o", bins[1]])
        sh(["gcc", "-O0", "-o", bins[2], c])
        sh(["gcc", "-O2", "-o", bins[3], c])
        sh(["gcc", "-O3", "-o", bins[4], c])
        res = [timeit(b) for b in bins]
        outs = set(o for (_, o) in res)
        rows.append((name, [t for (t, _) in res], len(outs) == 1, res[0][1]))

    w = max(len(r[0]) for r in rows) + 2
    print()
    print("%-*s" % (w, "bench") + "".join("%10s" % c for c in cols) + "  result")
    print("-" * (w + 10 * len(cols) + 10))
    for (name, ts, agree, out) in rows:
        print("%-*s" % (w, name) + "".join("%9.3fs" % t for t in ts) +
              "  " + (out if agree else "MISMATCH " + out))
    print("\nVIBE = native backend (no toolchain). VIBE -c = --backend=c"
          " (gcc -O3\nunder the hood). All outputs verified"
          " identical unless marked MISMATCH.")


if __name__ == "__main__":
    main()
