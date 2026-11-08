"""Resolve the dependency closure of a few Debian packages and report sizes."""
import io
import lzma
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "Packages.xz")
MIRROR = "https://mirrors.tuna.tsinghua.edu.cn/debian/dists/trixie/main/binary-amd64/Packages.xz"

TARGETS = ["xserver-xorg-core", "xserver-xorg-video-fbdev", "libgl1-mesa-dri",
           "libglx-mesa0", "xinit", "xauth", "libgl1", "libglvnd0"]


def load_packages():
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        req = urllib.request.Request(MIRROR, headers={"User-Agent": "python"})
        open(CACHE, "wb").write(urllib.request.urlopen(req, timeout=180).read())
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
            alt = part.split("|")[0].strip()
            name = re.split(r"[\s(]", alt)[0].strip()
            if name and not name.startswith("$"):
                out.append(name)
    return out


def main():
    pkgs = load_packages()
    seen = set()
    order = []
    stack = list(TARGETS)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        if name not in pkgs:
            print("not found:", name)
            continue
        seen.add(name)
        order.append(name)
        stack.extend(deps_of(pkgs[name]))
    total = 0
    for name in order:
        size = int(pkgs[name].get("Installed-Size", "0") or 0)
        total += size
    print("packages:", len(order), "approx installed MB:", round(total / 1024, 1))
    big = sorted(order, key=lambda n: -int(pkgs[n].get("Installed-Size", "0") or 0))[:15]
    for n in big:
        print("  %-35s %6.1f MB" % (n, int(pkgs[n].get("Installed-Size", "0") or 0) / 1024))
    io.open(os.path.join(ROOT, "out", "x11-packages.txt"), "w", encoding="utf-8").write("\n".join(order))


if __name__ == "__main__":
    main()
