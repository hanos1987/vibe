---
file: packaging/mkdeb.sh
file-hash: 55d365aacd7a003bb281af08262b5f40f7690b8a
note-hash: de8410bead2d3844
---

# packaging/mkdeb.sh

## What it is
Builds the `vibe_<version>_all.deb` Debian package into `packaging/out/`.

## How to navigate it
- Reads the version, sets maintainer (`VIBE_MAINTAINER` overrides).
- Lays out `usr/lib/vibe`, a `/usr/bin/vibec` shim, docs, examples.
- Writes copyright, changelog and a `vibec.1` man page inline, then `DEBIAN/control` and `md5sums`.
- Runs `dpkg-deb --build`.

## What it interacts with
- Reads `VERSION` from vibelang/cli.py; copies vibelang/, vibec, examples/*.vibe, README.md, SPEC.md, LICENSE.
- External: dpkg-deb, gzip, md5sum.
- Called by packaging/release.sh and packaging/mkrepo.sh.

## Why it exists
Provides the `.deb` for `apt install` and the APT repository.

## Helpful notes
Architecture is `all` (the compiler is Python). The inline man page lists `-o`, `--run`, `--ir`, `-O0`, `--version` but not `--backend=c` or `--check`.
