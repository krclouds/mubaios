#!/bin/sh
# Start Wine with the game's environment inside an existing X session.

PREFIX=/data/wine
ROOT=$PREFIX/root
export WINEPREFIX=/data/wineprefix
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="
export DISPLAY=:0
export LD_LIBRARY_PATH=$ROOT/usr/lib/x86_64-linux-gnu:$ROOT/usr/lib:$ROOT/usr/lib/wine
export PATH=$ROOT/usr/bin:$ROOT/usr/lib/wine:$PATH
export FONTCONFIG_PATH=$ROOT/etc/fonts

if [ ! -x "$ROOT/usr/bin/wine64" ] && [ ! -x "$ROOT/usr/lib/wine/wine64" ]; then
    echo "wine is not installed; run install-wine.sh first"
    exit 1
fi

mkdir -p "$WINEPREFIX"
if [ ! -d "$WINEPREFIX/drive_c" ]; then
    echo "initialising wine prefix (first run takes a minute)"
    "$ROOT/usr/bin/wineboot" -u >/tmp/wineboot.log 2>&1 || true
fi

exec "$ROOT/usr/bin/wine" "$@"
