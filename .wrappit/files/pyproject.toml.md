---
file: pyproject.toml
file-hash: 693807248f315c5ef35f8982e6696dc16d07b83e
note-hash: cad1f68394f626cf
---

# pyproject.toml

## What it is
Python packaging metadata for the `vibe-lang` package (the wheel/sdist and pip/pipx installs).

## How to navigate it
- `[build-system]`: setuptools.
- `[project]`: name, `version = "0.4.0"`, description, Python >= 3.8, MIT, classifiers.
- `[project.urls]`, then `[project.scripts]` mapping `vibec` to `vibelang.cli:main`.
- `[tool.setuptools]` packages `vibelang` plus `stdlib/*.vibe` as package data.

## What it interacts with
- `vibelang/cli.py` (entry point) and `vibelang/stdlib/*.vibe` (bundled data).
- README.md (used as the long description).
- packaging/release.sh builds the wheel/sdist from it with `python3 -m build`; install.ps1 pip-installs from it.

## Why it exists
Makes VIBE installable with pip/pipx and defines the installed `vibec` command.

## Helpful notes
The version here is typed by hand and must match `VERSION` in vibelang/cli.py (which the shell scripts read) and the `v0.4.0` links in README.md, site/vibe.html and site/check_page.py.
