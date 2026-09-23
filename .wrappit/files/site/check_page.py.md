---
file: site/check_page.py
file-hash: 2e84364986af83fe6d92acd443a1f4c7bf9ea43d
note-hash: 6457af7c69536a54
---

# site/check_page.py

## What it is
A structural checker for the generated page (default `site/dist/index.html`).

## How to navigate it
- `VOID` tags and a `REQUIRED` list of strings the page must contain.
- `Check`, an `HTMLParser` subclass that tracks open tags and reports mismatched or stray closes.
- `main()` prints ok/MISS per required string and any nesting problems; exits 1 on failure.

## What it interacts with
- Reads site/dist/index.html (made by site/build_page.py), or a path given as an argument.
- Python's `html.parser` only.

## Why it exists
Catches broken markup or a missing shell before the page is deployed.

## Helpful notes
`REQUIRED` hard-codes `releases/download/v0.4.0`; bump it with each release or the check fails.
