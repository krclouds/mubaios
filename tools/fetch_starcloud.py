import gzip
import io
import lzma
import os
import re
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
INCOMING = os.path.join(ROOT, "incoming")
os.makedirs(INCOMING, exist_ok=True)

URLS = {
    "deb": "https://starcloudfur.cn/downloads/starcloud-launcher-linux_0.3.8-beta.8_amd64.deb",
    "appimage": "https://starcloudfur.cn/downloads/Starcloud%20Launcher-0.3.8-beta.8.AppImage",
}


def download(url, dst):
    if os.path.exists(dst):
        return dst
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=300).read()
    open(dst, "wb").write(data)
    print("downloaded", os.path.basename(dst), round(len(data) / 1048576, 1), "MB")
    return dst


def ar_members(blob):
    if not blob.startswith(b"!<arch>\n"):
        raise SystemExit("not an ar archive")
    pos = 8
    while pos + 60 <= len(blob):
        h = blob[pos:pos + 60]
        name = h[0:16].decode("ascii", "replace").strip()
        size = int(h[48:58].decode("ascii").strip())
        yield name, blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)


def main():
    deb = download(URLS["deb"], os.path.join(INCOMING, "starcloud-launcher-linux_0.3.8-beta.8_amd64.deb"))
    blob = open(deb, "rb").read()
    control = data = None
    for name, payload in ar_members(blob):
        if name.startswith("control.tar"):
            control = (name, payload)
        elif name.startswith("data.tar"):
            data = (name, payload)
    print("members:", control[0], data[0])

    def open_tar(item):
        name, payload = item
        if name.endswith(".xz"):
            raw = lzma.decompress(payload)
        elif name.endswith(".gz"):
            raw = gzip.decompress(payload)
        else:
            raw = payload
        return tarfile.open(fileobj=io.BytesIO(raw), mode="r:")

    ctar = open_tar(control)
    ctrl = ctar.extractfile("./control").read().decode("utf-8", "ignore")
    print("---- control ----")
    print(ctrl[:1200])

    dtar = open_tar(data)
    total = 0
    biggest = []
    for m in dtar.getmembers():
        total += m.size
        if m.isfile():
            biggest.append((m.size, m.name))
    biggest.sort(reverse=True)
    print("files:", len(biggest), "unpacked MB:", round(total / 1048576, 1))
    for size, name in biggest[:15]:
        print("   %8.1f MB  %s" % (size / 1048576, name))

    # dependency scanning on the main ELF
    for m in dtar.getmembers():
        if not m.isfile() or m.size < 500000:
            continue
        name = m.name
        if "/resources/" in name or name.endswith((".so", ".pak", ".json", ".asar")):
            continue
        head = dtar.extractfile(m).read(64)
        if head[:4] != b"\x7fELF":
            continue
        print("---- ELF:", name, round(m.size / 1048576, 1), "MB")
        body = dtar.extractfile(m).read()
        libs = sorted(set(x.decode() for x in re.findall(rb"lib[a-zA-Z0-9_+.-]+\.so(?:\.\d+)*", body)))
        print("  libs:", libs[:30])
        interp = re.findall(rb"/lib64/[a-zA-Z0-9._-]+", body)
        print("  interp:", sorted(set(interp))[:3])


if __name__ == "__main__":
    main()
