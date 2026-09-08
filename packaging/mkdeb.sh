#!/bin/sh
# Build a Debian package for VIBE.
#
#   packaging/mkdeb.sh              -> packaging/out/vibe_<version>_all.deb
#   sudo apt install ./packaging/out/vibe_0.1.0_all.deb
#
# The compiler is Python, so the package is Architecture: all. The binaries
# it *emits* are x86-64 Linux, which the description states plainly.

set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
VERSION="$(sed -n 's/^VERSION = "\(.*\)"$/\1/p' "$ROOT/vibelang/cli.py")"
MAINTAINER="${VIBE_MAINTAINER:-Ben <benjfeir@protonmail.com>}"
OUT="$HERE/out"
PKG="$OUT/vibe_${VERSION}_all"

rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" \
         "$PKG/usr/lib/vibe" \
         "$PKG/usr/bin" \
         "$PKG/usr/share/doc/vibe" \
         "$PKG/usr/share/man/man1" \
         "$PKG/usr/share/vibe/examples"

cp -R "$ROOT/vibelang" "$PKG/usr/lib/vibe/vibelang"
cp    "$ROOT/vibec"    "$PKG/usr/lib/vibe/vibec"
cp    "$ROOT"/examples/*.vibe "$PKG/usr/share/vibe/examples/"
find "$PKG/usr/lib/vibe" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
chmod 0755 "$PKG/usr/lib/vibe/vibec"

cat > "$PKG/usr/bin/vibec" <<'SHIM'
#!/bin/sh
exec python3 /usr/lib/vibe/vibec "$@"
SHIM
chmod 0755 "$PKG/usr/bin/vibec"

cp "$ROOT/README.md" "$ROOT/SPEC.md" "$PKG/usr/share/doc/vibe/"

cat > "$PKG/usr/share/doc/vibe/copyright" <<COPY
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: vibe

Files: *
Copyright: 2026 Ben
License: MIT
COPY
sed 's/^/ /' "$ROOT/LICENSE" >> "$PKG/usr/share/doc/vibe/copyright"

cat > "$PKG/usr/share/doc/vibe/changelog.Debian" <<CHANGE
vibe ($VERSION) unstable; urgency=low

  * Initial release: sigil-based language, direct-to-machine-code compiler,
    standard library, examples.

 -- $MAINTAINER  $(date -R)
CHANGE
gzip -9n "$PKG/usr/share/doc/vibe/changelog.Debian"

cat > "$PKG/usr/share/man/man1/vibec.1" <<'MAN'
.TH VIBEC 1 "2026" "vibe" "User Commands"
.SH NAME
vibec \- compile VIBE source to a static x86-64 executable
.SH SYNOPSIS
.B vibec
.I file.vibe
.RB [ \-o
.IR out ]
.RB [ \-\-run ]
.RB [ \-\-ir ]
.RB [ \-O0 ]
.SH DESCRIPTION
.B vibec
compiles VIBE, a systems language whose every construct is a sigil rather
than a natural-language keyword. It writes ELF bytes directly: no assembler,
no linker and no C library take part, and the resulting executable is static
and depends on nothing.
.SH OPTIONS
.TP
.BI \-o " out"
Write the executable to
.IR out .
.TP
.B \-\-run
Compile to a temporary file, run it, and exit with its status.
.TP
.B \-\-ir
Print the mid-level intermediate representation instead of compiling.
.TP
.B \-O0
Disable optimisation and register allocation. Every value lives in memory.
Useful as an independent check on the optimiser.
.TP
.B \-\-version
Print the version and exit.
.SH FILES
.TP
.I /usr/lib/vibe/vibelang/stdlib/std.vibe
Standard library, itself written in VIBE. Include it with
.BR <<"std.vibe" .
.TP
.I /usr/share/vibe/examples
Worked programs: a terminal game, a wc clone, an HTTP server.
.SH SEE ALSO
The language reference at
.IR /usr/share/doc/vibe/SPEC.md .
MAN
gzip -9n "$PKG/usr/share/man/man1/vibec.1"

INSTALLED_KB="$(du -ks "$PKG" | cut -f1)"

cat > "$PKG/DEBIAN/control" <<CTRL
Package: vibe
Version: $VERSION
Section: devel
Priority: optional
Architecture: all
Depends: python3 (>= 3.8)
Installed-Size: $INSTALLED_KB
Maintainer: $MAINTAINER
Homepage: https://github.com/hanos1987/vibe
Description: programming language with no natural-language keywords
 VIBE is a systems language in which every construct is a sigil, compiled
 straight to machine code. The compiler writes ELF bytes itself: no
 assembler, no linker, no C library, and no runtime in the produced binary.
 .
 It has no operator precedence and no implicit conversions, which removes
 the two ambiguities that generated code most often gets wrong.
 .
 Ships a standard library written in VIBE, a language reference, and worked
 examples. Emitted executables are static Linux x86-64.
CTRL

find "$PKG" -path "$PKG/DEBIAN" -prune -o -type f -print \
  | sed "s|^$PKG/||" \
  | while read -r f; do
      printf '%s  %s\n' "$(md5sum "$PKG/$f" | cut -d' ' -f1)" "$f"
    done > "$PKG/DEBIAN/md5sums"

find "$PKG" -type d -exec chmod 0755 {} +
dpkg-deb --build --root-owner-group "$PKG" >/dev/null

echo "built $PKG.deb"
dpkg-deb --info "$PKG.deb" | sed -n '1,6p'
