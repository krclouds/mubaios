"""Resolve a Debian dependency closure and write a download list for the guest.

Usage: python tools/resolve_pkg.py out_name pkg1 pkg2 ...
Writes rootfs/system/share/<out_name>.txt with "<name> <pool path> <size>" lines.
"""
import lzma
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "Packages.xz")
MIRROR = "http://mirrors.aliyun.com/debian/dists/trixie/main/binary-amd64/Packages.xz"


def load_packages():
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        req = urllib.request.Request(MIRROR, headers={"User-Agent": "python"})
        open(CACHE, "wb").write(urllib.request.urlopen(req, timeout=300).read())
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
            name = re.split(r"[ (|\[]", part)[0]
            name = name.split(":")[0]
            if name:
                out.append(name)
    for rec in fields.get("Recommends", "").split(","):
        pass
    return out


def resolve(pkgs, targets):
    seen = {}
    stack = list(targets)
    while stack:
        name = stack.pop()
        if name in seen or name not in pkgs:
            continue
        f = pkgs[name]
        arch = f.get("Architecture", "")
        if arch not in ("amd64", "all"):
            continue
        seen[name] = f
        for d in deps_of(f):
            if d not in seen:
                stack.append(d)
    return seen


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    out_name = sys.argv[1]
    targets = sys.argv[2:]
    pkgs = load_packages()
    have = resolve(pkgs, targets)
    lines = []
    total = 0
    for name in sorted(have):
        f = have[name]
        size = int(f.get("Size", "0"))
        path = f.get("Filename")
        if not path:
            continue
        total += size
        lines.append("%s %s %d" % (name, path, size))
    dst = os.path.join(ROOT, "rootfs", "system", "share", out_name + ".txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("%d packages, %.1f MB -> %s" % (len(lines), total / 1048576.0, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
