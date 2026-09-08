#!/usr/bin/env python3
"""VIBE test runner.

Each tests/*.vibe declares its expectations in leading comments:
    ; out: <exact stdout line>
    ; exit: <exit status>
Each tests/err/*.vibe must fail to compile:
    ; err: <substring of the expected diagnostic>
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VIBEC = os.path.join(ROOT, "vibec")


def expectations(path):
    out, code, err = [], 0, None
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if not s.startswith(";"):
                if s:
                    break
                continue
            s = s[1:].strip()
            if s.startswith("out:"):
                out.append(s[4:].strip())
            elif s.startswith("exit:"):
                code = int(s[5:].strip())
            elif s.startswith("err:"):
                err = s[4:].strip()
    return out, code, err


def run_ok(path, extra):
    want_out, want_code, _ = expectations(path)
    tmp = tempfile.mktemp(prefix="vibetest-")
    c = subprocess.run([sys.executable, VIBEC, path, "-o", tmp] + extra,
                       capture_output=True, text=True)
    if c.returncode != 0:
        return False, "compile failed:\n" + c.stderr.strip()
    try:
        r = subprocess.run([tmp], capture_output=True, text=True, timeout=60)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    got = [l for l in r.stdout.split("\n") if l != ""]
    if got != want_out:
        return False, "stdout mismatch\n  want: %r\n  got:  %r" % (want_out, got)
    if r.returncode != want_code:
        return False, "exit %d, want %d" % (r.returncode, want_code)
    return True, ""


def run_err(path, extra):
    _, _, want = expectations(path)
    tmp = tempfile.mktemp(prefix="vibetest-")
    c = subprocess.run([sys.executable, VIBEC, path, "-o", tmp] + extra,
                       capture_output=True, text=True)
    if os.path.exists(tmp):
        os.unlink(tmp)
    if c.returncode == 0:
        return False, "expected a compile error, but it compiled"
    if want and want.lower() not in c.stderr.lower():
        return False, "wrong diagnostic\n  want substring: %r\n  got: %s" % (
            want, c.stderr.strip())
    return True, ""


def main(argv):
    extra = [a for a in argv[1:] if a.startswith("-")]
    npass = nfail = 0
    files = sorted(f for f in os.listdir(HERE) if f.endswith(".vibe"))
    for f in files:
        ok, why = run_ok(os.path.join(HERE, f), extra)
        print(("PASS " if ok else "FAIL ") + f + ("" if ok else "\n    " + why.replace("\n", "\n    ")))
        npass, nfail = npass + ok, nfail + (not ok)

    edir = os.path.join(HERE, "err")
    if os.path.isdir(edir):
        for f in sorted(x for x in os.listdir(edir) if x.endswith(".vibe")):
            ok, why = run_err(os.path.join(edir, f), extra)
            print(("PASS " if ok else "FAIL ") + "err/" + f +
                  ("" if ok else "\n    " + why.replace("\n", "\n    ")))
            npass, nfail = npass + ok, nfail + (not ok)

    print("\n%d passed, %d failed%s" % (npass, nfail,
                                        (" " + " ".join(extra)) if extra else ""))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
