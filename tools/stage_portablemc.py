import io
import lzma
import gzip
import os
import shutil
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTFS = os.path.join(ROOT, "rootfs")
CACHE = os.path.join(ROOT, "cache")

URL = "https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/g/gcc-14/libgcc-s1_14.2.0-19_amd64.deb"


def ar_members(blob):
    pos = 8
    while pos + 60 <= len(blob):
        h = blob[pos:pos + 60]
        name = h[0:16].decode("ascii", "replace").strip()
        size = int(h[48:58].decode("ascii").strip())
        yield name, blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python"})
    return urllib.request.urlopen(req, timeout=120).read()


def unpack(blob):
    for name, payload in ar_members(blob):
        if name.startswith("data.tar"):
            raw = lzma.decompress(payload) if name.endswith(".xz") else gzip.decompress(payload)
            return tarfile.open(fileobj=io.BytesIO(raw), mode="r:")
    raise SystemExit("no data.tar")


def main():
    deb = download(URL)
    print("deb", len(deb))
    tar = unpack(deb)
    target = None
    for m in tar.getmembers():
        if m.name.endswith("libgcc_s.so.1"):
            target = m
            break
    if not target:
        raise SystemExit("libgcc_s.so.1 not found")
    data = tar.extractfile(target).read()
    dst = os.path.join(ROOTFS, "lib/x86_64-linux-gnu/libgcc_s.so.1")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    print("libgcc_s", len(data))

    binary = os.path.join(CACHE, "portablemc")
    dst = os.path.join(ROOTFS, "system/bin/portablemc")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(binary, dst)
    print("portablemc staged", os.path.getsize(dst))


if __name__ == "__main__":
    main()
