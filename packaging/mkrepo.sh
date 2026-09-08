#!/bin/sh
# Build an APT repository so users can run `sudo apt install vibe`.
#
#   packaging/mkrepo.sh                       unsigned (needs [trusted=yes])
#   packaging/mkrepo.sh --sign <gpg-key-id>   signed, the normal case
#
# Upload packaging/apt/ to a static host, e.g. https://benjiapps.com/vibe/apt
# Then, on a user's machine:
#
#   curl -fsSL https://benjiapps.com/vibe/apt/vibe.gpg \
#     | sudo tee /usr/share/keyrings/vibe.gpg >/dev/null
#   echo "deb [signed-by=/usr/share/keyrings/vibe.gpg] \
#     https://benjiapps.com/vibe/apt stable main" \
#     | sudo tee /etc/apt/sources.list.d/vibe.list
#   sudo apt update && sudo apt install vibe

set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
REPO="$HERE/apt"
SIGNKEY=""
ORIGIN="${VIBE_ORIGIN:-vibe}"
SUITE="${VIBE_SUITE:-stable}"

while [ $# -gt 0 ]; do
    case "$1" in
        --sign) SIGNKEY="$2"; shift 2 ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "mkrepo.sh: unknown option $1" >&2; exit 2 ;;
    esac
done

command -v apt-ftparchive >/dev/null 2>&1 || {
    echo "mkrepo.sh: apt-ftparchive is required (apt install apt-utils)" >&2
    exit 1
}

sh "$HERE/mkdeb.sh" >/dev/null
DEB="$(ls -1 "$HERE/out"/vibe_*_all.deb | tail -1)"

rm -rf "$REPO"
mkdir -p "$REPO/pool/main/v/vibe" "$REPO/dists/$SUITE/main/binary-all"
cp "$DEB" "$REPO/pool/main/v/vibe/"

cd "$REPO"
apt-ftparchive packages pool > "dists/$SUITE/main/binary-all/Packages"
gzip -9kfn "dists/$SUITE/main/binary-all/Packages"

cat > /tmp/vibe-apt-release.conf <<CONF
APT::FTPArchive::Release::Origin "$ORIGIN";
APT::FTPArchive::Release::Label "VIBE";
APT::FTPArchive::Release::Suite "$SUITE";
APT::FTPArchive::Release::Codename "$SUITE";
APT::FTPArchive::Release::Architectures "all";
APT::FTPArchive::Release::Components "main";
APT::FTPArchive::Release::Description "The VIBE programming language";
CONF
apt-ftparchive -c /tmp/vibe-apt-release.conf release "dists/$SUITE" \
    > "dists/$SUITE/Release"
rm -f /tmp/vibe-apt-release.conf

if [ -n "$SIGNKEY" ]; then
    rm -f "dists/$SUITE/Release.gpg" "dists/$SUITE/InRelease"
    gpg --default-key "$SIGNKEY" -abs -o "dists/$SUITE/Release.gpg" \
        "dists/$SUITE/Release"
    gpg --default-key "$SIGNKEY" --clearsign -o "dists/$SUITE/InRelease" \
        "dists/$SUITE/Release"
    gpg --export "$SIGNKEY" > "$REPO/vibe.gpg"
    echo "signed with $SIGNKEY; public key written to apt/vibe.gpg"
else
    echo "NOT signed. Users must add [trusted=yes] to their sources line,"
    echo "which apt warns about. Re-run with --sign <key-id> for a real repo."
fi

echo "repository built at $REPO"
find "$REPO" -type f | sed "s|^$REPO|  apt|" | sort
