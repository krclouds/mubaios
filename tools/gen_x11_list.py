"""Emit the X11 + Mesa package list (name, deb path) for the runtime installer."""
import io
import lzma
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "Packages.xz")
MIRROR = "https://mirrors.tuna.tsinghua.edu.cn/debian/dists/trixie/main/binary-amd64/Packages.xz"
OUT = os.path.join(ROOT, "rootfs", "system", "share", "x11-packages.txt")

TARGETS = ["xserver-xorg-core", "xserver-xorg-video-fbdev", "libgl1-mesa-dri",
           "libglx-mesa0", "xinit", "xauth", "libgl1", "libglvnd0",
           "xserver-xorg-input-evdev", "xkb-data"]


def load_packages():
    raw = lzma.decompress(open(CACHE, "rb").read()).decode("utf-8", "ignore")
    pkgs = {}
    for stanza in raw.split("\n\n"):
        if not stanza.strip():
            continue
        fields = {}
        for line in stanza.splitlines():
            if line[:1] in (" ", "\t"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        name = fields.get("Package")
        if name and name not in pkgs:
            pkgs[name] = fields
    return pkgs


def deps_of(fields):
    out = []
    for key in ("Depends", "Pre-Depends"):
        for part in fields.get(key, "").split(","):
            part = part.strip()
            if not part:
                continue
            name = re.split(r"[\s(]", part.split("|")[0].strip())[0].strip()
            if name and not name.startswith("$"):
                out.append(name)
    return out


def main():
    pkgs = load_packages()
    seen, order, stack = set(), [], list(TARGETS)
    while stack:
        name = stack.pop()
        if name in seen or name not in pkgs:
            continue
        seen.add(name)
        order.append(name)
        stack.extend(deps_of(pkgs[name]))

    lines = []
    total = 0
    for name in order:
        f = pkgs[name]
        filename = f.get("Filename", "")
        size = int(f.get("Installed-Size", "0") or 0)
        total += size
        lines.append("%s %s %d" % (name, filename, size))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("packages:", len(lines), "installed MB:", round(total / 1024, 1), "->", OUT)


if __name__ == "__main__":
    main()
