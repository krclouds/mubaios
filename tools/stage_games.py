"""Download the game packages on the host and unpack them into rootfs/opt/games."""
import io
import os
import sys
import tarfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "rootfs", "system", "share", "games-packages.txt")
CACHE = os.path.join(ROOT, "cache", "games")
DEST = os.path.join(ROOT, "rootfs", "opt", "games")
MIRROR = "http://mirrors.aliyun.com/debian"


def ar_members(data):
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("not an ar archive")
    pos = 8
    while pos + 60 <= len(data):
        header = data[pos:pos + 60]
        name = header[0:16].decode("ascii", "replace").strip()
        size = int(header[48:58].decode("ascii", "replace").strip())
        pos += 60
        body = data[pos:pos + size]
        pos += size + (size & 1)
        yield name.rstrip("/"), body


def extract_deb(path, dest):
    data = open(path, "rb").read()
    for name, body in ar_members(data):
        if not name.startswith("data.tar"):
            continue
        if name.endswith(".xz"):
            blob = __import__("lzma").decompress(body)
        elif name.endswith(".gz"):
            blob = __import__("gzip").decompress(body)
        elif name.endswith(".zst"):
            raise ValueError("zstd data.tar not supported")
        else:
            blob = body
        with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
            for m in tf.getmembers():
                if m.name.startswith("./"):
                    m.name = m.name[2:]
                if not m.name or m.name.startswith(".."):
                    continue
                tf.extract(m, dest, set_attrs=False)
        return True
    return False


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)
    lines = [l.split() for l in open(LIST, encoding="utf-8").read().splitlines() if l.strip()]
    ok = fail = 0
    for name, path, size in lines:
        deb = os.path.join(CACHE, name + ".deb")
        if not os.path.exists(deb) or os.path.getsize(deb) != int(size):
            url = MIRROR + "/" + path
            for attempt in range(3):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "python"})
                    data = urllib.request.urlopen(req, timeout=120).read()
                    open(deb, "wb").write(data)
                    break
                except Exception as exc:
                    if attempt == 2:
                        print("fail", name, exc)
                        fail += 1
                        continue
                    time.sleep(1)
        try:
            if extract_deb(deb, DEST):
                ok += 1
            else:
                fail += 1
        except Exception as exc:
            print("unpack fail", name, exc)
            fail += 1
    print("extracted %d, failed %d -> %s" % (ok, fail, DEST))


if __name__ == "__main__":
    sys.exit(main())
