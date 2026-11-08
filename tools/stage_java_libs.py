"""Add the remaining glibc stubs + zlib that the JDK needs."""
import gzip
import io
import lzma
import os
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTFS = os.path.join(ROOT, "rootfs")
CACHE = os.path.join(ROOT, "cache")

LIBC6 = ("https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/g/glibc/"
         "libc6_2.41-12+deb13u4_amd64.deb")
ZLIB = ("https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/z/zlib/"
        "zlib1g_1.3.dfsg+really1.3.1-1+b2_amd64.deb")

WANTED = ["libpthread.so.0", "libdl.so.2", "librt.so.1", "libutil.so.1",
          "libresolv.so.2", "libz.so.1"]


def ar_members(blob):
    pos = 8
    while pos + 60 <= len(blob):
        h = blob[pos:pos + 60]
        name = h[0:16].decode("ascii", "replace").strip()
        size = int(h[48:58].decode("ascii").strip())
        yield name, blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)


def get(url, name):
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "python"})
        open(path, "wb").write(urllib.request.urlopen(req, timeout=180).read())
    return open(path, "rb").read()


def open_data(blob):
    for name, payload in ar_members(blob):
        if name.startswith("data.tar"):
            raw = lzma.decompress(payload) if name.endswith(".xz") else gzip.decompress(payload)
            return tarfile.open(fileobj=io.BytesIO(raw), mode="r:")
    raise SystemExit("no data.tar")


def install(deb, wanted):
    tar = open_data(deb)
    found = {}
    for m in tar.getmembers():
        base = m.name.split("/")[-1]
        if base in wanted and m.isfile():
            found[base] = tar.extractfile(m).read()
    for base, data in found.items():
        dst = os.path.join(ROOTFS, "lib/x86_64-linux-gnu", base)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(data)
        print("installed", base, len(data))
    missing = [w for w in wanted if w not in found]
    if missing:
        print("missing:", missing)


install(get(LIBC6, "libc6-new.deb"), ["libpthread.so.0", "libdl.so.2", "librt.so.1",
                                      "libutil.so.1", "libresolv.so.2"])
install(get(ZLIB, "zlib1g.deb"), ["libz.so.1"])
