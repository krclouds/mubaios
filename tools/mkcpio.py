#!/usr/bin/env python3
"""A tiny, dependency-free cpio (newc) writer.

The Linux kernel unpacker for initramfs reads "newc" archives, which is also
what `find | cpio -o -H newc | gzip` produces.  Doing it in pure Python means
TinyLinux can be assembled on Windows without any Linux tools at all, and we
can put device nodes, symlinks and ownership directly into the image.
"""
import gzip
import os
import struct
import sys

S_IFDIR = 0o040000
S_IFREG = 0o100000
S_IFLNK = 0o120000
S_IFCHR = 0o020000

MAGIC = b"070701"
HEADER_LEN = 110


class CpioArchive:
    def __init__(self):
        self.items = []  # (name, mode, data, rdev)

    # -- building ---------------------------------------------------
    def add_dir(self, path, mode=0o755):
        self.items.append((path, S_IFDIR | mode, b"", None))

    def add_file(self, path, data, mode=0o644):
        if isinstance(data, str):
            data = data.encode()
        self.items.append((path, S_IFREG | mode, data, None))

    def add_file_from(self, path, source, mode=0o644):
        with open(source, "rb") as f:
            self.add_file(path, f.read(), mode)

    def add_symlink(self, path, target):
        self.items.append((path, S_IFLNK | 0o777, target.encode(), None))

    def add_device(self, path, major, minor, mode=0o600):
        self.items.append((path, S_IFCHR | mode, b"", (major, minor)))

    # -- serialising ------------------------------------------------
    def to_bytes(self):
        out = bytearray()
        ino = 1
        # Parents must be unpacked before their children.
        for name, mode, data, rdev in sorted(self.items, key=lambda e: (e[0].strip("/").count("/"), e[0])):
            name = name.lstrip("/")
            rdev_major, rdev_minor = rdev if rdev else (0, 0)
            fields = (
                ino, mode, 0, 0, 2 if (mode & 0o170000) == S_IFDIR else 1,
                0, len(data), 0, 0, rdev_major, rdev_minor, len(name) + 1, 0,
            )
            out += MAGIC
            out += b"".join(b"%08X" % (f & 0xFFFFFFFF) for f in fields)
            out += name.encode() + b"\0"
            out += b"\0" * ((4 - (HEADER_LEN + len(name) + 1) % 4) % 4)
            out += data
            out += b"\0" * ((4 - len(data) % 4) % 4)
            ino += 1

        # trailer
        out += MAGIC
        out += b"".join(b"%08X" % f for f in (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 11, 0))
        out += b"TRAILER!!!\0"
        out += b"\0" * ((4 - (HEADER_LEN + 11) % 4) % 4)
        return bytes(out)

    def write(self, path, compress=True):
        raw = self.to_bytes()
        if compress:
            with open(path, "wb") as f:
                f.write(gzip.compress(raw, 9, mtime=0))
        else:
            with open(path, "wb") as f:
                f.write(raw)
        return len(raw)


if __name__ == "__main__":
    # Quick manual use: mkcpio.py out.cpio.gz dir1 dir2 ...
    arc = CpioArchive()
    dst = sys.argv[1]
    for root in sys.argv[2:]:
        for dirpath, dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            prefix = "" if rel == "." else rel.replace(os.sep, "/") + "/"
            arc.add_dir(prefix or ".", os.stat(dirpath).st_mode & 0o7777)
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                if os.path.islink(full):
                    arc.add_symlink(prefix + fn, os.readlink(full))
                else:
                    arc.add_file_from(prefix + fn, full, os.stat(full).st_mode & 0o7777)
    print("wrote %s (%d bytes)" % (dst, arc.write(dst)))
