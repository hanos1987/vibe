---
file: site/vibe.html
file-hash: 7402198b4b4e39b50bd07e5c328c48769b5311ab
note-hash: a05222836e423409
---

# site/vibe.html

## What it is
The source of the VIBE web page (hero, install, language, examples, benchmarks) without a full HTML document shell.

## How to navigate it
- `<title>`, Google Fonts links, then one big `<style>` block.
- `<header class="top">` nav, then `<main>`: hero, `#why` (three rules), `#install` (tabbed apt / Linux-macOS / pip / Windows / source panels plus download links), `#language`, `#built`, `#speed`, footer.
- A closing `<script>` for the install tabs (arrow keys) and COPY buttons.

## What it interacts with
- site/build_page.py reads it to make site/dist/index.html.
- Links: GitHub repo, SPEC.md, release downloads, install.sh, install.ps1, benjiapps.com/vibe/apt; fonts from fonts.googleapis.com.

## Why it exists
The single source for both the artifact and the benjiapps.com page.

## Helpful notes
Release links and the footer hard-code `0.4.0`; bump them with each release, then rerun site/build_page.py. Don't edit dist/index.html directly.
