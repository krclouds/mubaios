import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def drop_lines(path, needles):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("missing", path)
        return
    src = open(p, encoding="utf-8").read().splitlines(True)
    out = [l for l in src if not any(n in l for n in needles)]
    removed = len(src) - len(out)
    open(p, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("%s: removed %d line(s)" % (path, removed))


# 1. drop the world app from the build and the store catalogue
drop_lines("build.py", ['"world": {"manifest"'])
drop_lines("src/store.c", ['{"world", "迷你世界"'])

# 2. delete the source file
world_c = os.path.join(ROOT, "src", "world.c")
if os.path.exists(world_c):
    os.remove(world_c)
    print("deleted src/world.c")

# 3. translation entries for the removed app
drop_lines("src/nova.c", ['{"迷你世界", "Mini World"}'])

# 4. glyph special-case for the world icon
p = os.path.join(ROOT, "src", "system_server.c")
s = open(p, encoding="utf-8").read()
s = s.replace('	if (!strcmp(a->id, "world")) {\n\t\tdraw_world_glyph(fb, cx, cy, s, fg);\n\t\treturn;\n\t}\n', "")
open(p, "w", encoding="utf-8", newline="\n").write(s)

# 5. docs
p = os.path.join(ROOT, "APPS.md")
if os.path.exists(p):
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"\n## .*迷你世界.*?(?=\n## )", "\n", s, flags=re.S)
    s = s.replace("迷你世界", "方块沙盒")
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("APPS.md cleaned")
print("done")
