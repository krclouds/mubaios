#!/usr/bin/env python3
"""Build a bootable CD image for mubaiOS.

ISOLINUX is the CD bootloader; pycdlib lays out the ISO 9660 filesystem and the
El Torito boot catalog.  The kernel and the initramfs (with all the DRM/input
modules inside) are copied onto the disc, so the ISO boots on its own.

Output: out/mubaios-0.2-x86_64.iso
"""
import io
import os
import re
import socket
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

OUT = os.path.join(ROOT, "out")
CACHE = os.path.join(ROOT, "cache")
SYSLINUX_DIR = os.path.join(CACHE, "syslinux")
ISO_PATH = os.path.join(OUT, "mubaios-0.2-x86_64.iso")

DEBIAN = "https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/s/syslinux"
DEBS = {
    "isolinux": DEBIAN + "/isolinux_6.04~git20190206.bf6db5b4%2Bdfsg1-3.2_all.deb",
    "syslinux-common": DEBIAN + "/syslinux-common_6.04~git20190206.bf6db5b4%2Bdfsg1-3.2_all.deb",
}

ISOLINUX_CFG = """\
# mubaiOS boot menu -- ISOLINUX, the CD-ROM flavour of SYSLINUX.
SERIAL 0 115200
PROMPT 1
TIMEOUT 50
DEFAULT nova

LABEL nova
  KERNEL /BOOT/BZIMAGE
  INITRD /BOOT/INITRD.IMG
  APPEND console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0

LABEL debug
  KERNEL /BOOT/BZIMAGE
  INITRD /BOOT/INITRD.IMG
  APPEND console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1
"""

README_TXT = """\
mubaiOS 0.2 -- a self-built desktop system on the Linux kernel.

Boot this CD in a BIOS/CSM machine or a virtual machine.  The graphical shell
starts automatically on the framebuffer (1280x800); use the mouse, or attach a
touch panel.

Keyboard: Esc leaves an app.  The default entry starts the UI only; the
"debug" entry also opens a shell on the serial console.
"""


def step(msg):
    print("\033[36m==>\033[0m %s" % msg)


def die(msg):
    print("\033[31merror:\033[0m %s" % msg)
    sys.exit(1)


def ensure_pycdlib():
    try:
        import pycdlib  # noqa: F401
        return
    except ImportError:
        pass
    dest = os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "toolchain", "pylib")
    if os.path.isdir(dest):
        sys.path.insert(0, dest)
        try:
            import pycdlib  # noqa: F401
            return
        except ImportError:
            pass
    dest = os.path.join(OUT, "toolchain", "pylib")
    step("fetching pycdlib")
    index = "https://pypi.tuna.tsinghua.edu.cn/simple/pycdlib/"
    html = urllib.request.urlopen(index, timeout=60).read().decode("utf-8", "replace")
    wheels = [urllib.parse.urljoin(index, u) for u in re.findall(r'href="([^"#]+\.whl)', html)]
    wheel = [u for u in wheels if "py3-none-any" in u][-1]
    data = urllib.request.urlopen(wheel, timeout=60).read()
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(dest)
    sys.path.insert(0, dest)


def extract_deb(deb_path, wanted, dest):
    os.makedirs(dest, exist_ok=True)
    with open(deb_path, "rb") as f:
        if f.read(8) != b"!<arch>\n":
            raise RuntimeError("not a .deb")
        while True:
            hdr = f.read(60)
            if len(hdr) < 60:
                break
            name = hdr[0:16].decode().strip().rstrip("/")
            size = int(hdr[48:58].decode().strip())
            body = f.read(size)
            if size % 2:
                f.read(1)
            if not name.startswith("data.tar"):
                continue
            with tarfile.open(fileobj=io.BytesIO(body), mode="r:*") as tar:
                for member in tar.getmembers():
                    base = os.path.basename(member.name)
                    if base in wanted and member.isfile():
                        with open(os.path.join(dest, base), "wb") as out:
                            out.write(tar.extractfile(member).read())


def ensure_syslinux():
    shared = os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "cache", "syslinux")
    for name in ("isolinux.bin", "ldlinux.c32"):
        if not os.path.exists(os.path.join(SYSLINUX_DIR, name)) and os.path.exists(os.path.join(shared, name)):
            os.makedirs(SYSLINUX_DIR, exist_ok=True)
            with open(os.path.join(shared, name), "rb") as src, open(os.path.join(SYSLINUX_DIR, name), "wb") as dst:
                dst.write(src.read())

    missing = [n for n in ("isolinux.bin", "ldlinux.c32")
               if not os.path.exists(os.path.join(SYSLINUX_DIR, n))]
    if not missing:
        return
    for pkg, url in DEBS.items():
        deb = os.path.join(CACHE, pkg + ".deb")
        if not os.path.exists(deb):
            step("fetching %s" % pkg)
            with urllib.request.urlopen(url, timeout=120) as resp:
                with open(deb, "wb") as f:
                    f.write(resp.read())
    step("extracting ISOLINUX")
    extract_deb(os.path.join(CACHE, "isolinux.deb"), {"isolinux.bin"}, SYSLINUX_DIR)
    extract_deb(os.path.join(CACHE, "syslinux-common.deb"), {"ldlinux.c32"}, SYSLINUX_DIR)
    for n in missing:
        if not os.path.exists(os.path.join(SYSLINUX_DIR, n)):
            die("could not extract %s" % n)


def build_iso():
    import pycdlib

    kernel = os.path.join(OUT, "nova.bzImage")
    initrd = os.path.join(OUT, "nova-initramfs.cpio.gz")
    for p in (kernel, initrd):
        if not os.path.exists(p):
            die("%s missing -- run python build.py first" % p)

    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident="NOVAOS")
    iso.add_directory("/BOOT", joliet_path="/BOOT")
    iso.add_directory("/ISOLINUX", joliet_path="/ISOLINUX")

    def add(path, data, iso_dir, joliet=None):
        kwargs = {"joliet_path": joliet} if joliet else {}
        iso.add_fp(io.BytesIO(data), len(data), "%s/%s;1" % (iso_dir, path), **kwargs)

    for name in ("ISOLINUX.BIN", "LDLINUX.C32"):
        with open(os.path.join(SYSLINUX_DIR, name.lower()), "rb") as f:
            add(name, f.read(), "/ISOLINUX")
    add("ISOLINUX.CFG", ISOLINUX_CFG.encode(), "/ISOLINUX")
    add("README.TXT", README_TXT.encode(), "/")
    with open(kernel, "rb") as f:
        add("BZIMAGE", f.read(), "/BOOT", joliet="/BOOT/NOVA.BZIMAGE")
    with open(initrd, "rb") as f:
        add("INITRD.IMG", f.read(), "/BOOT", joliet="/BOOT/NOVA-INITRAMFS.CPIO.GZ")

    step("writing El Torito boot catalog")
    iso.add_eltorito("/ISOLINUX/ISOLINUX.BIN;1",
                     bootcatfile="/ISOLINUX/BOOT.CAT;1",
                     media_name="noemul",
                     boot_load_size=4,
                     boot_info_table=True)

    step("writing %s" % os.path.basename(ISO_PATH))
    iso.write(ISO_PATH)
    iso.close()


def main():
    socket.setdefaulttimeout(120)
    for p in (os.path.join(OUT, "nova.bzImage"), os.path.join(OUT, "nova-initramfs.cpio.gz")):
        if not os.path.exists(p):
            die("run python build.py first")
    ensure_pycdlib()
    ensure_syslinux()
    build_iso()
    step("done")
    print("    iso : %s (%.1f MiB)" % (ISO_PATH, os.path.getsize(ISO_PATH) / 1048576.0))


if __name__ == "__main__":
    main()
