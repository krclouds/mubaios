import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "rootfs", "system", "bin", "install-games.sh")
s = open(p, encoding="utf-8").read()

s = s.replace('TMP=/tmp/gamedeb', 'TMP=/tmp/gamedeb\nVER=2')
s = s.replace('if [ -f "$PREFIX/.installed-$1" ]; then', 'if [ -f "$PREFIX/.installed$VER-$1" ]; then')
s = s.replace('touch "$PREFIX/.installed-$1"', '''if [ "$ok" -gt 0 ]; then
    touch "$PREFIX/.installed$VER-$1"
fi''')
s = s.replace('count=0', 'count=0\nok=0')
s = s.replace('    busybox dpkg-deb -x "$deb" "$ROOT" 2>/dev/null || echo "[warn] unpack: $name"',
              '    if busybox dpkg-deb -x "$deb" "$ROOT" 2>/dev/null; then\n        ok=$((ok + 1))\n    else\n        echo "[warn] unpack: $name"\n    fi')
s = s.replace('echo "done: games installed under $ROOT"', 'echo "done: $ok/$count packages under $ROOT"')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print(s)
