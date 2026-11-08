import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "rootfs", "system", "bin", "install-games.sh")
s = open(p, encoding="utf-8").read()
old = 'LIST="/system/share/${1:-games-packages}.txt"'
new = 'LIST="/system/share/games-${1:-packages}.txt"'
assert old in s, "pattern not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("list path:", new)
