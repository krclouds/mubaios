import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def drop_block(path, start_marker, end_marker="\n"):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()
    i = s.find(start_marker)
    if i < 0:
        print("marker not found in", path)
        return
    j = s.find(end_marker, i)
    s = s[:i] + s[j + len(end_marker):]
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("removed block from", path)


# 1. build.py: stop packaging the Minecraft shell app
drop_block("build.py",
           '    # Minecraft ships as a shell app: the launcher only needs an executable',
           '    for app_id, info in STORE_APPS.items():')

# 2. delete the app payloads / runtime pieces that only existed for Minecraft
targets = [
    ("rootfs/system/bin/minecraft.sh", "file"),
    ("rootfs/system/bin/portablemc", "file"),
    ("rootfs/opt/jdk", "dir"),
    ("rootfs/apps/hello", "dir"),
]
for rel, kind in targets:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print("absent", rel)
        continue
    if kind == "dir":
        shutil.rmtree(p)
    else:
        os.remove(p)
    print("deleted", rel)

# 3. docs: drop the Minecraft / hello sections
p = os.path.join(ROOT, "APPS.md")
if os.path.exists(p):
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"\n## .*(我的世界|Minecraft|hello).*?(?=\n## )", "\n", s, flags=re.S)
    s = s.replace("我的世界", "minecraft")
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("APPS.md cleaned")

print("done")
