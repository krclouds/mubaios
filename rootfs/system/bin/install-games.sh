#!/bin/sh
# Install a small set of Debian games (bsdgames + luanti) into /data/games/root.
set -e

PREFIX=/data/games
ROOT=$PREFIX/root
LIST="/system/share/games-${1:-packages}.txt"
MIRROR=http://mirrors.aliyun.com/debian
TMP=/tmp/gamedeb
VER=2

if [ -f "$PREFIX/.installed$VER-$1" ]; then
    echo "games already installed"
    exit 0
fi

mkdir -p "$ROOT" "$TMP"
echo "installing games (about 74 MB)"

count=0
ok=0
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
    if busybox dpkg-deb -x "$deb" "$ROOT" 2>/dev/null; then
        ok=$((ok + 1))
    else
        echo "[warn] unpack: $name"
    fi
    rm -f "$deb"
    if [ $((count % 20)) -eq 0 ]; then
        echo "  $count/$total"
    fi
done < "$LIST"

if [ "$ok" -gt 0 ]; then
    touch "$PREFIX/.installed$VER-$1"
fi
echo "done: $ok/$count packages under $ROOT"
