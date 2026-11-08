import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

REPL = {
    "about.c": [("自研用户态 + Linux 内核的类 Android 系统", "自研用户态 + Linux 内核的桌面系统")],
    "init.c": [(" * mubaiOS is a small Android-shaped system built directly on the Linux kernel.",
                " * mubaiOS is a small desktop system built directly on the Linux kernel.")],
    "inputd.c": [(" * This is the same idea as Android's InputManager: apps never care where an",
                  " * Same idea as Android's InputManager (design inspiration only): apps never care where an")],
    "nova.c": [('{"基于 Linux 内核的桌面系统", "An Android-shaped system on the Linux kernel"}',
                '{"基于 Linux 内核的桌面系统", "A desktop system on the Linux kernel"}')],
}

for name, pairs in REPL.items():
    p = os.path.join(SRC, name)
    s = open(p, encoding="utf-8").read()
    o = s
    for a, b in pairs:
        s = s.replace(a, b)
    if s != o:
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        print("patched", name)
print("done")
