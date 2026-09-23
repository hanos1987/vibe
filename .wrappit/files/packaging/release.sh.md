---
file: packaging/release.sh
file-hash: cc19bbceef7f86a0f42702bcebc92983fc103e5d
note-hash: c228daf9d66b782b
---

# packaging/release.sh

## What it is
Builds every downloadable release file into `packaging/out/`.

## How to navigate it
Four marked blocks in order: source tarball (copies a fixed list of repo items, strips caches/`.bin`), Debian package (calls mkdeb.sh), Python wheel and sdist (only if the `build` module is installed), then `SHA256SUMS`.

## What it interacts with
- Reads `VERSION` from vibelang/cli.py.
- Runs packaging/mkdeb.sh.
- Tarball includes vibelang/, vibec, examples/, tests/, bench/, tools/, packaging/, README.md, SPEC.md, LICENSE, install.sh, install.ps1, pyproject.toml.
- External: tar, sha256sum, `python3 -m build`; output is uploaded with `gh release create`.

## Why it exists
One command to produce the release assets that README.md and site/vibe.html link to.

## Helpful notes
The wheel version comes from pyproject.toml but the tarball/deb version from vibelang/cli.py, so both must be bumped together. Wheel failures are reported but do not stop the script.
