"""Fetch a glibc runtime and a sample package for NovaOS's deb support.

Pure Python: the .deb is an ar archive, and its data member is a tar that may be
gzip/xz compressed.  We only keep the few files the runtime needs, so the image
grows by ~2.5 MB instead of a full libc6 install.
"""
import gzip
import io
import lzma
import os
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
ROOTFS = os.path.join(ROOT, "rootfs")

DEBS = {
    "libc6": "https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/g/glibc/libc6_2.41-12+deb13u4_amd64.deb",
    "hello": "https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/h/hello/hello_2.10-5_amd64.deb",
}

WANTED = [
    "lib/x86_64-linux-gnu/libc.so.6",
    "lib/x86_64-linux-gnu/libm.so.6",
    "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
]


def download(name, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".deb")
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "python"})
        data = urllib.request.urlopen(req, timeout=120).read()
        open(path, "wb").write(data)
        print("downloaded", name, len(data))
    return path


def ar_members(blob):
    """Yield (name, bytes) for an ar archive."""
    if not blob.startswith(b"!<arch>\n"):
        raise SystemExit("not an ar archive")
    pos = 8
    while pos + 60 <= len(blob):
        header = blob[pos:pos + 60]
        name = header[0:16].decode("ascii", "replace").strip()
        size = int(header[48:58].decode("ascii").strip())
        data = blob[pos + 60:pos + 60 + size]
        yield name, data
        pos += 60 + size + (size & 1)


def data_member(blob):
    for name, data in ar_members(blob):
        if name.startswith("data.tar"):
            return name, data
    raise SystemExit("no data.tar member")


def unpack(blob):
    name, data = data_member(blob)
    if name.endswith(".xz"):
        raw = lzma.decompress(data)
    elif name.endswith(".gz"):
        raw = gzip.decompress(data)
    else:
        raise SystemExit("unsupported member " + name)
    return tarfile.open(fileobj=io.BytesIO(raw), mode="r:")


def main():
    libc = download("libc6", DEBS["libc6"])
    blob = open(libc, "rb").read()
    tar = unpack(blob)
    by_name = {}
    for m in tar.getmembers():
        by_name.setdefault(m.name.split("/")[-1], m)
    for rel in WANTED:
        base = rel.split("/")[-1]
        m = by_name.get(base)
        if m is None:
            raise SystemExit("missing " + rel)
        dst = os.path.join(ROOTFS, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(tar.extractfile(m).read())
        print("installed", rel, os.path.getsize(dst))

    loader = os.path.join(ROOTFS, "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2")
    dst64 = os.path.join(ROOTFS, "lib64/ld-linux-x86-64.so.2")
    os.makedirs(os.path.dirname(dst64), exist_ok=True)
    open(dst64, "wb").write(open(loader, "rb").read())
    print("installed lib64 loader")

    hello = download("hello", DEBS["hello"])
    samples = os.path.join(ROOTFS, "samples")
    os.makedirs(samples, exist_ok=True)
    open(os.path.join(samples, "hello.deb"), "wb").write(open(hello, "rb").read())
    print("sample deb:", os.path.getsize(os.path.join(samples, "hello.deb")))


if __name__ == "__main__":
    main()
