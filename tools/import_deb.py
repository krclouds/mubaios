import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ar_members(blob):
    if not blob.startswith(b"!<arch>\n"):
        raise SystemExit("not an ar archive")
    pos = 8
    while pos + 60 <= len(blob):
        header = blob[pos:pos + 60]
        name = header[0:16].decode("ascii", "replace").strip()
        size = int(header[48:58].decode("ascii").strip())
        yield name, blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)


def import_deb(path, rootfs):
    """Unpack a .deb into rootfs/ and register it in /apps."""
    import gzip
    import lzma
    import tarfile

    blob = open(path, "rb").read()
    data = None
    for name, payload in ar_members(blob):
        if name.startswith("data.tar"):
            data = (name, payload)
            break
    if data is None:
        raise SystemExit("no data.tar in " + path)
    name, payload = data
    if name.endswith(".xz"):
        raw = lzma.decompress(payload)
    elif name.endswith(".gz"):
        raw = gzip.decompress(payload)
    else:
        raise SystemExit("unsupported compression in " + path)

    tar = tarfile.open(fileobj=io.BytesIO(raw), mode="r:")
    files = []
    for m in tar.getmembers():
        if not m.isfile():
            continue
        rel = m.name.lstrip("./")
        if not rel or rel.startswith("etc/") or rel.startswith("var/"):
            continue
        dst = os.path.join(rootfs, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(tar.extractfile(m).read())
        os.chmod(dst, 0o755 if (m.mode & 0o111) else 0o644)
        files.append(rel)

    exe = None
    for rel in files:
        base = os.path.basename(rel)
        if rel.startswith(("usr/bin/", "bin/", "usr/sbin/", "sbin/")) and not base.endswith(".so"):
            exe = rel
            break
    if exe is None:
        raise SystemExit("no executable in " + path)

    pkg = os.path.splitext(os.path.basename(path))[0]
    app_id = "".join(c if c.isalnum() else "_" for c in pkg.lower())
    app_dir = os.path.join(rootfs, "apps", app_id)
    os.makedirs(app_dir, exist_ok=True)
    wrapper = ("#!/bin/sh\nexec /lib64/ld-linux-x86-64.so.2 "
               "--library-path /lib/x86_64-linux-gnu /%s \"$@\"\n" % exe)
    open(os.path.join(app_dir, app_id), "w", encoding="utf-8", newline="\n").write(wrapper)
    os.chmod(os.path.join(app_dir, app_id), 0o755)
    manifest = "name=%s\nicon=%s\ncolor=8e44ad\norder=300\n" % (pkg, pkg[:1].upper())
    open(os.path.join(app_dir, "manifest"), "w", encoding="utf-8", newline="\n").write(manifest)
    print("imported deb %s -> /apps/%s (exe /%s)" % (pkg, app_id, exe))
    return app_id


if __name__ == "__main__":
    import_deb(sys.argv[1], os.path.join(ROOT, "rootfs"))
