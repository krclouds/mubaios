#!/bin/sh
# Install a Wine prefix into /data/wine/root by unpacking Debian packages.
set -e

PREFIX=/data/wine
ROOT=$PREFIX/root
LIST=/system/share/wine-packages.txt
MIRROR=http://mirrors.aliyun.com/debian
TMP=/tmp/winedeb

if [ -f "$PREFIX/.installed" ]; then
    echo "wine already installed"
    exit 0
fi

mkdir -p "$ROOT" "$TMP"
echo "installing wine (about 180 MB)"

count=0
total=$(wc -l < "$LIST")
while read -r name path size; do
    [ -z "$name" ] && continue
    count=$((count + 1))
    deb=$TMP/$name.deb
    if [ ! -s "$deb" ]; then
        wget -q -U novaos -O "$deb" "$MIRROR/$path" || {
            echo "[warn] failed: $name"
            rm -f "$deb"
            continue
        }
    fi
    busybox dpkg-deb -x "$deb" "$ROOT" 2>/dev/null || echo "[warn] unpack: $name"
    rm -f "$deb"
    if [ $((count % 25)) -eq 0 ]; then
        echo "  $count/$total"
    fi
done < "$LIST"

# Wine needs its own libs first, plus the X client libraries.
mkdir -p "$PREFIX/bin"
ln -sf "$ROOT/usr/lib/wine/wine64" "$PREFIX/bin/wine64" 2>/dev/null || true
ln -sf "$ROOT/usr/bin/wine64" "$PREFIX/bin/wine64" 2>/dev/null || true
ln -sf "$ROOT/usr/bin/wine" "$PREFIX/bin/wine" 2>/dev/null || true
ln -sf "$ROOT/usr/bin/wineserver" "$PREFIX/bin/wineserver" 2>/dev/null || true

touch "$PREFIX/.installed"
echo "done: wine installed under $ROOT"
