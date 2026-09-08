#!/bin/sh
# Build every downloadable artifact for a VIBE release.
#
#   packaging/release.sh
#
# Produces, in packaging/out/:
#   vibe-<version>.tar.gz        source tarball (contains install.sh)
#   vibe_<version>_all.deb       Debian/Ubuntu package
#   vibe-<version>-py3-none-any.whl  and .tar.gz sdist, when `build` is present
#   SHA256SUMS                   checksums for all of the above

set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
VERSION="$(sed -n 's/^VERSION = "\(.*\)"$/\1/p' "$ROOT/vibelang/cli.py")"
OUT="$HERE/out"
mkdir -p "$OUT"

echo "VIBE $VERSION"

# --- source tarball ---------------------------------------------------------
STAGE="$(mktemp -d)"
DIR="$STAGE/vibe-$VERSION"
mkdir -p "$DIR"
for item in vibelang vibec examples tests bench tools packaging \
            README.md SPEC.md LICENSE install.sh install.ps1 pyproject.toml; do
    [ -e "$ROOT/$item" ] && cp -R "$ROOT/$item" "$DIR/"
done
rm -rf "$DIR/packaging/out" "$DIR/packaging/apt"
find "$DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$DIR" -name '*.pyc' -delete 2>/dev/null || true
find "$DIR" -name '*.bin' -delete 2>/dev/null || true
rm -f "$OUT/vibe-$VERSION.tar.gz"
tar -C "$STAGE" -czf "$OUT/vibe-$VERSION.tar.gz" "vibe-$VERSION"
rm -rf "$STAGE"
echo "  source tarball"

# --- debian package ---------------------------------------------------------
sh "$HERE/mkdeb.sh" >/dev/null
echo "  debian package"

# --- python wheel and sdist -------------------------------------------------
if python3 -c "import build" 2>/dev/null; then
    (cd "$ROOT" && python3 -m build --outdir "$OUT" >/dev/null 2>&1) \
        && echo "  wheel and sdist" \
        || echo "  wheel skipped (build failed)"
else
    echo "  wheel skipped (pip install build)"
fi

# --- checksums --------------------------------------------------------------
cd "$OUT"
rm -f SHA256SUMS
# shellcheck disable=SC2035
sha256sum *.tar.gz *.deb *.whl 2>/dev/null | grep -v 'SHA256SUMS' > SHA256SUMS \
    || sha256sum *.tar.gz *.deb > SHA256SUMS
echo
echo "artifacts in $OUT:"
ls -1sh *.tar.gz *.deb *.whl 2>/dev/null | sed 's/^/  /'
echo
cat SHA256SUMS
