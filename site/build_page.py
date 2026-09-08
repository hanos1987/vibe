#!/usr/bin/env python3
"""Wrap site/vibe.html into a standalone page for benjiapps.com.

The artifact host supplies a document shell; a hosted page needs its own.
This generates site/dist/index.html from the same source, so the artifact
and the live page can never drift apart.

  python3 site/build_page.py
"""

import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "vibe.html")
DIST = os.path.join(HERE, "dist")

DESCRIPTION = (
    "VIBE is a systems language with no natural-language keywords, compiled "
    "straight to x86-64 machine code. No assembler, no linker, no libc."
)

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
    "%3Crect width='100' height='100' rx='22' fill='%230f1426'/%3E"
    "%3Ctext x='50' y='68' font-size='54' text-anchor='middle' fill='%23f2a93b'"
    " font-family='monospace' font-weight='bold'%3E@!%3C/text%3E%3C/svg%3E"
)

ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">\
<circle cx="9" cy="12" r="6.2" stroke="white" stroke-width="2"/>\
<circle cx="9" cy="12" r="2.1" stroke="white" stroke-width="2"/>\
<path d="M18.5 6.5v8" stroke="white" stroke-width="2" stroke-linecap="round"/>\
<circle cx="18.5" cy="18" r="1.15" fill="white"/></svg>
"""


def build():
    with open(SRC) as fh:
        content = fh.read()

    end = content.index("</style>") + len("</style>")
    head, body = content[:end], content[end:]

    # the source's own <title> becomes the page title; give the hosted copy a
    # descriptive one instead, since it is a public web page
    head = head.replace("<title>VIBE</title>", "", 1)

    # a way back to the storefront this page lives in
    body = body.replace(
        '<nav class="top-links">',
        '<nav class="top-links">\n      <a href="/" class="home">&larr; benjiapps</a>',
        1,
    )

    doc = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="%s">
<meta property="og:title" content="VIBE">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<title>VIBE &mdash; a programming language made of sigils</title>
<link rel="icon" href="%s">
%s
<style>
  html { color-scheme: dark; }
  body { margin: 0; }
  img { max-width: 100%%; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
%s
</body>
</html>
""" % (DESCRIPTION, DESCRIPTION, FAVICON, head.strip(), body.strip())

    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "index.html")
    with open(out, "w") as fh:
        fh.write(doc)
    with open(os.path.join(DIST, "icon.svg"), "w") as fh:
        fh.write(ICON)

    print("wrote %s (%d bytes)" % (out, len(doc)))
    print("wrote %s" % os.path.join(DIST, "icon.svg"))

    # sanity: the wrapper must not have dropped anything
    for needle in ("<h1", "Install VIBE", "sigils", "</html>", "SHA256SUMS"):
        if needle not in doc:
            raise SystemExit("build_page: %r missing from output" % needle)
    if doc.count("<style") != 2:
        raise SystemExit("build_page: unexpected number of style blocks")
    print("checks passed")


if __name__ == "__main__":
    build()
