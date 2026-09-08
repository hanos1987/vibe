#!/bin/sh
# VIBE installer for Linux and macOS.
#
#   ./install.sh                      install from a checkout
#   ./install.sh --prefix ~/.local    choose where it goes
#   curl -fsSL <url>/install.sh | sh  fetch and install
#
# Needs python3, and git only when fetching. The compiler has no other
# dependencies, and the binaries it produces have none at all.
#
# Note: vibec emits static Linux x86-64 executables. It runs anywhere
# python3 runs, but on macOS the programs it compiles need a Linux host
# (a container or VM) to execute.

set -eu

REPO="${VIBE_REPO:-https://github.com/hanos1987/vibe.git}"
PREFIX="${VIBE_PREFIX:-$HOME/.local}"

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix) PREFIX="$2"; shift 2 ;;
        --prefix=*) PREFIX="${1#--prefix=}"; shift ;;
        -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "vibe: python3 is required to run the compiler" >&2
    exit 1
fi

OS="$(uname -s)"
ARCH="$(uname -m)"

SRC=""
CLEAN=""
if [ -f "$(dirname "$0")/vibec" ] && [ -d "$(dirname "$0")/vibelang" ]; then
    SRC="$(cd "$(dirname "$0")" && pwd)"
else
    command -v git >/dev/null 2>&1 || {
        echo "vibe: git is required to fetch the source" >&2; exit 1; }
    SRC="$(mktemp -d)"
    CLEAN="$SRC"
    echo "fetching $REPO"
    git clone --depth 1 --quiet "$REPO" "$SRC"
fi

SHARE="$PREFIX/share/vibe"
BIN="$PREFIX/bin"
mkdir -p "$SHARE" "$BIN"

rm -rf "$SHARE/vibelang"
cp -R "$SRC/vibelang" "$SHARE/vibelang"
cp "$SRC/vibec" "$SHARE/vibec"
for f in SPEC.md README.md LICENSE; do
    [ -f "$SRC/$f" ] && cp "$SRC/$f" "$SHARE/$f"
done
[ -d "$SRC/examples" ] && { rm -rf "$SHARE/examples"; cp -R "$SRC/examples" "$SHARE/examples"; }
chmod +x "$SHARE/vibec"
find "$SHARE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

cat > "$BIN/vibec" <<EOF
#!/bin/sh
exec python3 "$SHARE/vibec" "\$@"
EOF
chmod +x "$BIN/vibec"

[ -n "$CLEAN" ] && rm -rf "$CLEAN"

echo "installed vibec to $BIN/vibec"
echo "language reference: $SHARE/SPEC.md"
echo "examples:           $SHARE/examples"

case ":$PATH:" in
    *":$BIN:"*) ;;
    *) printf '\nadd it to your PATH:\n    export PATH="%s:$PATH"\n' "$BIN" ;;
esac

if [ "$OS" != "Linux" ]; then
    printf '\nnote: vibec runs here, but it emits Linux x86-64 executables.\n'
    printf 'run them on a Linux host, in a container, or under a VM.\n'
elif [ "$ARCH" != "x86_64" ]; then
    printf '\nnote: this machine is %s; vibec emits x86-64 binaries.\n' "$ARCH"
fi

printf '\ntry it:\n'
printf '    cat > hello.vibe <<%s\n' "'EOF'"
printf '@! () s64 {\n'
printf '  $ s %%Str = "hello from VIBE\\n"\n'
printf '  \\1(1, s.p, s.n)\n'
printf '  ^ 0\n'
printf '}\n'
printf 'EOF\n'
printf '    vibec hello.vibe -o hello && ./hello\n'
