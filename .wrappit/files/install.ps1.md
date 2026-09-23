---
file: install.ps1
file-hash: 870903a54be9995664c7ac7dfc96f45f9894a560
note-hash: e2f50ab56f8a5bc0
---

# install.ps1

## What it is
The Windows PowerShell installer; it installs vibec with `pip install --user`.

## How to navigate it
- Help block and a `-Repo` parameter.
- `Find-Python` tries `py -3`, `python3`, `python` and needs 3.8+.
- Installs from the local checkout if pyproject.toml is beside the script, otherwise from `git+<Repo>`.
- Finds the user Scripts folder, suggests a PATH change, prints WSL instructions.

## What it interacts with
- pyproject.toml (the local-install marker and what pip builds).
- External: Python/pip, GitHub (hanos1987/vibe), WSL for running output.
- Linked from README.md and site/vibe.html; bundled by packaging/release.sh.

## Why it exists
Gives Windows users a one-line install; compiling works natively, running output needs WSL.

## Helpful notes
It does not edit PATH itself, it only prints the command to do so.
