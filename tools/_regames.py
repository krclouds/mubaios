import lzma
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import resolve_pkg

FRESH = os.path.join(ROOT, "cache", "Packages-fresh.xz")
MIRROR = "http://mirrors.aliyun.com/debian/dists/trixie/main/binary-amd64/Packages.xz"

if not os.path.exists(FRESH) or os.path.getsize(FRESH) < 1000000:
    req = urllib.request.Request(MIRROR, headers={"User-Agent": "python"})
    data = urllib.request.urlopen(req, timeout=300).read()
    open(FRESH, "wb").write(data)
    print("downloaded Packages.xz", len(data))

raw = lzma.decompress(open(FRESH, "rb").read()).decode("utf-8", "ignore")
pkgs = {}
for stanza in raw.split("\n\n"):
    fields = {}
    for line in stanza.splitlines():
        if line[:1] in (" ", "\t") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip()
    name = fields.get("Package")
    if name and name not in pkgs:
        pkgs[name] = fields

for target, out in (("bsdgames", "games-core"), ("bsdgames luanti", "games-packages")):
    want = resolve_pkg.resolve(pkgs, target.split())
    lines = []
    total = 0
    for name in sorted(want):
        f = want[name]
        path = f.get("Filename")
        if not path:
            continue
        total += int(f.get("Size", "0"))
        lines.append("%s %s %s" % (name, path, f.get("Size", "0")))
    dst = os.path.join(ROOT, "rootfs", "system", "share", out + ".txt")
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(out, len(lines), "packages", round(total / 1048576.0, 1), "MB")
