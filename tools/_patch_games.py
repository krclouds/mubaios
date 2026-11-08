import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

p = os.path.join(ROOT, "rootfs", "system", "bin", "install-games.sh")
s = open(p, encoding="utf-8").read().replace("\r\n", "\n")
s = s.replace("LIST=/system/share/games-packages.txt",
              'LIST="/system/share/${1:-games-packages}.txt"')
s = s.replace("if [ -f \"$PREFIX/.installed\" ]; then",
              "if [ -f \"$PREFIX/.installed-$1\" ]; then")
s = s.replace("touch \"$PREFIX/.installed\"", "touch \"$PREFIX/.installed-$1\"")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("list param:", "${1:-games-packages}" in s)
