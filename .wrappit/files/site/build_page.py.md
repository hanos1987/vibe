---
file: site/build_page.py
file-hash: 1036edfe8767df67cdaa76b375a51329e1b66d8c
note-hash: 2aabb29cccc39ba1
---

# site/build_page.py

## What it is
Turns site/vibe.html into the standalone public page `site/dist/index.html` for benjiapps.com.

## How to navigate it
- Constants: `DESCRIPTION`, `FAVICON` (inline SVG data URL), `ICON`.
- `build()`: splits the source at `</style>`, drops its `<title>`, adds a "back to benjiapps" link in the nav, wraps it in a full HTML document, writes `dist/index.html` and `dist/icon.svg`, then runs sanity checks.

## What it interacts with
- Reads site/vibe.html; writes site/dist/index.html and site/dist/icon.svg.
- site/check_page.py checks its output; site/entry.json points at `icon.svg`.

## Why it exists
Keeps one source for both the artifact version and the hosted page so they cannot drift.

## Helpful notes
Its checks require `Install VIBE`, `SHA256SUMS` and exactly two `<style` blocks in the output; editing vibe.html can trip them. The byte count it prints is characters, not bytes.
