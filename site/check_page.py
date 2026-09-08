#!/usr/bin/env python3
"""Structural check on the generated standalone page.

  python3 site/check_page.py [path]

Catches the failures that matter for a hosted page: mismatched or unclosed
elements, and a missing document shell.
"""

import os
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

REQUIRED = [
    "<!DOCTYPE html>",
    'data-theme="dark"',
    "</html>",
    'id="install"',
    "releases/download/v0.1.0",
    "github.com/hanos1987/vibe",
]


class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.problems.append("stray </%s> at %s" % (tag, self.getpos()))
            return
        top, pos = self.stack.pop()
        if top != tag:
            self.problems.append(
                "</%s> at %s closes <%s> opened at %s"
                % (tag, self.getpos(), top, pos))


def main(argv):
    path = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist", "index.html")
    with open(path) as fh:
        src = fh.read()

    c = Check()
    c.feed(src)
    if c.stack:
        c.problems.append("unclosed: %s" % [t for t, _ in c.stack])

    print("%s (%d bytes)" % (path, len(src)))
    bad = False
    for needle in REQUIRED:
        ok = needle in src
        bad = bad or not ok
        print("  %s %s" % ("ok  " if ok else "MISS", needle))
    if c.problems:
        bad = True
        for p in c.problems:
            print("  PROBLEM %s" % p)
    else:
        print("  ok   element nesting balanced")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
