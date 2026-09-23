---
file: packaging/mkrepo.sh
file-hash: 14ecf7b9938b2fea6cefce766fea8d2083845c97
note-hash: a8087bba97c9f09d
---

# packaging/mkrepo.sh

## What it is
Builds a static APT repository in `packaging/apt/` so users can `sudo apt install vibe`.

## How to navigate it
- Header shows user setup commands for benjiapps.com/vibe/apt; `--sign <key-id>` option.
- Requires `apt-ftparchive`, runs mkdeb.sh, copies the newest .deb into `pool/`.
- Generates `Packages`, `Packages.gz`, and a `Release` file from a temp config.
- With `--sign`: `Release.gpg`, `InRelease`, and the exported public key `vibe.gpg`; otherwise warns it is unsigned.

## What it interacts with
- Runs packaging/mkdeb.sh; uses its `packaging/out/` output.
- External: apt-ftparchive, gpg, the benjiapps.com static host.
- README.md and site/vibe.html give users the matching sources line.

## Why it exists
Lets Debian/Ubuntu users get VIBE and updates through apt with a signed repo.

## Helpful notes
It deletes and rebuilds `packaging/apt/` each run. Upload to benjiapps.com is manual. Env vars `VIBE_ORIGIN`/`VIBE_SUITE` change origin and suite (default `stable`).
