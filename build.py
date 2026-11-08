#!/usr/bin/env python3
"""Build mubaiOS: kernel + modules + our own user space.

Pipeline:
  cache/linux-image.deb  --[extract]--> out/nova.bzImage + out/modules/
  src/*.c                --[zig cc]-->  out/build/*
  rootfs + modules + busybox + binaries --[mkcpio]--> out/nova-initramfs.cpio.gz

No root, no Linux installation: the kernel package is unpacked with Python and
the initramfs is written by tools/mkcpio.py.
"""
import argparse
import glob
import io
import os
import shutil
import subprocess
import sys
import tarfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

from mkcpio import CpioArchive  # noqa: E402

OUT = os.path.join(ROOT, "out")
CACHE = os.path.join(ROOT, "cache")
DEB = os.path.join(CACHE, "linux-image.deb")

# Modules mubaiOS needs at boot, in dependency order.  Everything else stays in
# the kernel package; only this list goes into the initramfs.
MODULES_ALPINE = [
    "kernel/drivers/virtio/virtio.ko",
    "kernel/drivers/virtio/virtio_ring.ko",
    "kernel/drivers/virtio/virtio_pci_legacy_dev.ko",
    "kernel/drivers/virtio/virtio_pci_modern_dev.ko",
    "kernel/drivers/virtio/virtio_pci.ko",
    "kernel/drivers/gpu/drm/drm.ko",
    "kernel/drivers/gpu/drm/drm_kms_helper.ko",
    "kernel/drivers/gpu/drm/drm_shmem_helper.ko",
    "kernel/drivers/virtio/virtio_dma_buf.ko",
    "kernel/drivers/gpu/drm/virtio/virtio-gpu.ko",
    "kernel/drivers/input/evdev.ko",
    "kernel/drivers/input/misc/uinput.ko",
    "kernel/drivers/input/mouse/psmouse.ko",
    "kernel/drivers/usb/common/usb-common.ko",
    "kernel/drivers/usb/core/usbcore.ko",
    "kernel/drivers/usb/host/uhci-hcd.ko",
    "kernel/drivers/hid/hid.ko",
    "kernel/drivers/hid/usbhid/usbhid.ko",
    "kernel/drivers/hid/hid-generic.ko",
    "kernel/net/core/failover.ko",
    "kernel/drivers/net/net_failover.ko",
    "kernel/drivers/net/virtio_net.ko",
    "kernel/drivers/block/virtio_blk.ko",
    "kernel/lib/crc16.ko",
    "kernel/fs/mbcache.ko",
    "kernel/fs/jbd2/jbd2.ko",
    "kernel/fs/ext4/ext4.ko",
    "kernel/crypto/crc32c_generic.ko",
    "kernel/arch/x86/crypto/crc32c-intel.ko",
]

MODULES_DEBIAN = [
    "kernel/drivers/gpu/drm/drm.ko",
    "kernel/drivers/gpu/drm/drm_kms_helper.ko",
    "kernel/drivers/gpu/drm/ttm/ttm.ko",
    "kernel/drivers/gpu/drm/drm_ttm_helper.ko",
    "kernel/drivers/gpu/drm/drm_vram_helper.ko",
    "kernel/drivers/gpu/drm/tiny/bochs.ko",
    "kernel/drivers/input/evdev.ko",
    "kernel/drivers/input/misc/uinput.ko",
    "kernel/drivers/input/mouse/psmouse.ko",
    "kernel/drivers/usb/common/usb-common.ko",
    "kernel/drivers/usb/core/usbcore.ko",
    "kernel/drivers/usb/host/uhci-hcd.ko",
    "kernel/drivers/hid/hid.ko",
    "kernel/drivers/hid/usbhid/usbhid.ko",
    "kernel/drivers/hid/hid-generic.ko",
    "kernel/drivers/virtio/virtio.ko",
    "kernel/drivers/virtio/virtio_ring.ko",
    "kernel/drivers/virtio/virtio_pci_legacy_dev.ko",
    "kernel/drivers/virtio/virtio_pci_modern_dev.ko",
    "kernel/drivers/virtio/virtio_pci.ko",
    "kernel/net/core/failover.ko",
	"kernel/drivers/net/net_failover.ko",
	"kernel/drivers/net/virtio_net.ko",
	"kernel/drivers/block/virtio_blk.ko",
	"kernel/lib/crc16.ko",
	"kernel/fs/mbcache.ko",
	"kernel/fs/jbd2/jbd2.ko",
	"kernel/fs/ext4/ext4.ko",
	"kernel/crypto/crc32c_generic.ko",
	"kernel/arch/x86/crypto/crc32c-intel.ko",
]

# mubaiOS boots the Debian kernel by default; NOVA_KERNEL=alpine picks the
# Alpine one, which is the only one with a virtio-gpu driver (3D via virgl).
KERNEL_KIND = os.environ.get("NOVA_KERNEL", "debian")
MODULES = MODULES_ALPINE if KERNEL_KIND == "alpine" else MODULES_DEBIAN

# Installed applications: id -> source file + manifest shown on the home screen.
APPS = {
    "settings": {"manifest": "name=设置\nicon=设\ncolor=6c5ce7\norder=10\n"},
    "files": {"manifest": "name=文件\nicon=文\ncolor=f39c12\norder=20\n"},
    "paint": {"manifest": "name=画板\nicon=画\ncolor=1abc9c\norder=30\n"},
    "terminal": {"manifest": "name=终端\nicon=终\ncolor=0f766e\norder=40\n"},
    "store": {"manifest": "name=应用商店\nicon=店\ncolor=8e44ad\norder=50\n"},
    "licenses": {"manifest": "name=开源许可\nicon=许\ncolor=0ea5e9\norder=55\n"},
}

# Apps that live in the store payload (/store) and are copied into /apps when
# the user taps install.
STORE_APPS = {
    "clock": {"manifest": "name=时钟\nicon=钟\ncolor=2980b9\norder=60\n"},
    "calc": {"manifest": "name=计算器\nicon=算\ncolor=16a085\norder=70\n"},
    "snake": {"manifest": "name=贪吃蛇\nicon=蛇\ncolor=c0392b\norder=80\n"},
    "calendar": {"manifest": "name=日历\nicon=历\ncolor=e67e22\norder=100\n"},
    "weather": {"manifest": "name=天气\nicon=天\ncolor=3498db\norder=110\n"},
    "gallery": {"manifest": "name=相册\nicon=相\ncolor=8e44ad\norder=120\n"},
    "music": {"manifest": "name=钢琴\nicon=乐\ncolor=e84393\norder=130\n"},
    "notes": {"manifest": "name=便签\nicon=签\ncolor=f1c40f\norder=140\n"},
    "minesweeper": {"manifest": "name=扫雷\nicon=雷\ncolor=7f8c8d\norder=150\n"},
    "game2048": {"manifest": "name=2048\nicon=数\ncolor=16a085\norder=160\n"},
    "stopwatch": {"manifest": "name=秒表\nicon=秒\ncolor=d35400\norder=170\n"},
    "sysmon": {"manifest": "name=系统监视\nicon=监\ncolor=2c3e50\norder=180\n"},
    "compass": {"manifest": "name=指南针\nicon=针\ncolor=c0392b\norder=190\n"},
    "about": {"manifest": "name=关于\nicon=关\ncolor=95a5a6\norder=200\n"},
}

APPLETS = """
[ [[ ash awk cat chgrp chmod chown clear cp cut date dd df dirname dmesg echo
egrep env expr false free grep dpkg dpkg-deb basename find gunzip gzip head hostname id ifconfig kill less
ln ls md5sum mke2fs mkdir mknod more mount mv nc netstat od pidof ping poweroff ps pwd
readlink reboot rm rmdir route sed seq sh sleep sort stat sync tail tar tee
test time top touch tr true tty umount uname uniq uptime vi wc wget xargs yes
""".split()


def step(msg):
    print("\033[36m==>\033[0m %s" % msg)


def die(msg):
    print("\033[31merror:\033[0m %s" % msg)
    sys.exit(1)


def find_zig():
    candidates = [
        os.path.join(ROOT, "out", "toolchain", "zig"),
        os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "toolchain", "zig"),
    ]
    for base in candidates:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in ("zig.exe", "zig"):
                if fn in filenames:
                    return os.path.join(dirpath, fn)
    die("Zig not found -- copy it from tinylinux/out/toolchain or run tinylinux/tools/fetch_assets.py")


def extract_deb(data, wanted):
    """Return {archive name: bytes} for members under ./lib/modules or ./boot."""
    if data[:8] != b"!<arch>\n":
        die("not a .deb")
    out = {}
    pos = 8
    while pos + 60 <= len(data):
        hdr = data[pos:pos + 60]
        name = hdr[0:16].decode().strip().rstrip("/")
        size = int(hdr[48:58].decode().strip())
        body = data[pos + 60:pos + 60 + size]
        pos += 60 + size + (size % 2)
        if not name.startswith("data.tar"):
            continue
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:*") as tar:
            for member in tar.getmembers():
                norm = member.name[2:] if member.name.startswith("./") else member.name
                for w in wanted:
                    if w.lstrip("/") in norm:
                        out[norm] = tar.extractfile(member).read()
    return out


def unpack_alpine_kernel():
    src = os.path.join(OUT, "alpine")
    vmlinuz = os.path.join(src, "vmlinuz-lts")
    if not os.path.isfile(vmlinuz):
        die("missing %s -- run tools/prep_alpine.py" % vmlinuz)

    kver = "6.6.142-0-lts"
    step("using the Alpine kernel (virtio-gpu capable)")
    shutil.copyfile(vmlinuz, os.path.join(OUT, "nova.bzImage"))

    dest_root = os.path.join(OUT, "modules", "lib", "modules")
    if os.path.isdir(dest_root):
        shutil.rmtree(dest_root)
    dest = os.path.join(dest_root, kver)
    os.makedirs(dest, exist_ok=True)
    src_mods = os.path.join(src, "modules")
    for dirpath, _dirnames, filenames in os.walk(src_mods):
        rel = os.path.relpath(dirpath, src_mods)
        for fn in filenames:
            if not fn.endswith(".ko"):
                continue
            target = os.path.join(dest, rel, fn)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(dirpath, fn), target)
    step("extracted %d modules for %s" % (len(MODULES), kver))
    return kver


def unpack_kernel():
    os.makedirs(OUT, exist_ok=True)
    if KERNEL_KIND == "alpine":
        return unpack_alpine_kernel()
    if not os.path.exists(DEB):
        die("missing %s -- run tools/fetch.py" % DEB)

    step("unpacking the kernel package")
    with open(DEB, "rb") as f:
        data = f.read()
    members = extract_deb(data, ["/boot/vmlinuz-", "/modules.dep"])
    kver = None
    for name in members:
        if name.startswith("boot/vmlinuz-"):
            kver = name.split("boot/vmlinuz-")[1]
            with open(os.path.join(OUT, "nova.bzImage"), "wb") as f:
                f.write(members[name])
    if not kver:
        die("vmlinuz not found in the kernel package")

    modules_dir = os.path.join(OUT, "modules", "lib", "modules", kver)
    if os.path.isdir(os.path.dirname(modules_dir)):
        shutil.rmtree(os.path.dirname(modules_dir))
    os.makedirs(modules_dir, exist_ok=True)

    step("extracting %d modules for %s" % (len(MODULES), kver))
    wanted = ["/" + m for m in MODULES]
    found = extract_deb(data, wanted)
    missing = [m for m in MODULES if not any(k.endswith(m) for k in found)]
    for name, blob in found.items():
        dest = os.path.join(OUT, "modules", name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(blob)
    for m in missing:
        print("    [warn] module not in package: %s" % m)
    return kver


def ensure_fonts():
    """Regenerate font_cjk.h when the sources use characters it lacks."""
    import re

    used = set()
    for name in os.listdir(os.path.join(ROOT, "src")):
        if name.endswith((".c", ".h")) and not name.startswith("font_") and name != "font8x16.h":
            text = open(os.path.join(ROOT, "src", name), encoding="utf-8", errors="ignore").read()
            used.update(re.findall(r"[\u3000-\u9fff\uff00-\uffef]", text))
    try:
        header = open(os.path.join(ROOT, "src", "font_cjk.h"), encoding="utf-8").read()
    except OSError:
        header = ""
    have = {chr(int(m, 16)) for m in re.findall(r"\{0x([0-9a-f]{4}), \{", header)}
    missing = used - have
    if missing:
        step("font_cjk.h is missing %d characters, regenerating" % len(missing))
        subprocess.run([sys.executable, os.path.join(TOOLS, "genfont.py")], check=True)


def build_binaries(zig):
    os.makedirs(os.path.join(OUT, "build"), exist_ok=True)
    env = dict(os.environ)
    env["ZIG_GLOBAL_CACHE_DIR"] = os.path.join(OUT, "zig-cache")
    env["ZIG_LOCAL_CACHE_DIR"] = os.path.join(OUT, "zig-cache")

    sources = sorted(glob.glob(os.path.join(ROOT, "src", "*.c")))
    sources = [s for s in sources if os.path.basename(s) not in ("nova.c",)]
    built = {}
    for src in sources:
        name = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(OUT, "build", name)
        cmd = [zig, "cc", "-target", "x86_64-linux-musl", "-static", "-Os", "-s",
               "-fno-stack-protector", "-Wall", "-Wextra", "-Wno-unused-parameter",
               "-I", os.path.join(ROOT, "src"), "-o", out, src,
               os.path.join(ROOT, "src", "nova.c"), "-lm"]
        print("    cc %s" % name)
        res = subprocess.run(cmd, env=env)
        if res.returncode != 0:
            die("compiling %s failed" % name)
        built[name] = out
    return built


def build_rootfs(zig, kver):
    busybox = os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "cache", "busybox")
    if not os.path.isfile(busybox):
        die("BusyBox not found at %s" % busybox)

    ensure_fonts()
    step("compiling Nova user space")
    built = build_binaries(zig)

    arc = CpioArchive()
    for d, mode in [
        ("bin", 0o755), ("sbin", 0o755), ("etc", 0o755), ("dev", 0o755),
        ("proc", 0o555), ("sys", 0o555), ("tmp", 0o1777), ("run", 0o755),
        ("root", 0o700), ("usr", 0o755), ("usr/bin", 0o755),
        ("var", 0o755), ("lib", 0o755), ("system", 0o755), ("system/bin", 0o755),
        ("apps", 0o755), ("data", 0o755), ("store", 0o755), ("store/apps", 0o755),
    ]:
        arc.add_dir(d, mode)

    arc.add_file_from("init", built["init"], 0o755)
    arc.add_file_from("system/bin/system_server", built["system_server"], 0o755)
    arc.add_file_from("bin/input", built["input"], 0o755)
    arc.add_file_from("system/bin/inputd", built["inputd"], 0o755)

    for app_id, info in APPS.items():
        d = "apps/" + app_id
        arc.add_dir(d, 0o755)
        arc.add_file_from(d + "/" + app_id, built[app_id], 0o755)
        arc.add_file(d + "/manifest", info["manifest"], 0o644)

    for app_id, info in STORE_APPS.items():
        d = "store/apps/" + app_id
        arc.add_dir(d, 0o755)
        arc.add_file_from(d + "/" + app_id, built[app_id], 0o755)
        arc.add_file(d + "/manifest", info["manifest"], 0o644)
    arc.add_file_from("bin/busybox", busybox, 0o755)
    for applet in APPLETS:
        arc.add_symlink("bin/" + applet, "/bin/busybox")
    arc.add_file("etc/modules", "\n".join(MODULES) + "\n", 0o644)
    arc.add_symlink("sbin/init", "/init")

    for src_dir in (os.path.join(OUT, "modules"), os.path.join(ROOT, "rootfs")):
        dirs = {}
        files = []
        for dirpath, _dirnames, filenames in os.walk(src_dir):
            rel = os.path.relpath(dirpath, src_dir).replace(os.sep, "/")
            rel = "" if rel == "." else rel
            if rel:
                dirs[rel] = 0o755
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                target = (rel + "/" + fn) if rel else fn
                files.append((target, full))
        for d in sorted(dirs, key=lambda p: p.count("/")):
            arc.add_dir(d, dirs[d])
        for target, full in files:
            exe = (target.endswith((".ko", ".sh")) or ".so" in os.path.basename(target)
                   or "/bin/" in ("/" + target) or "/sbin/" in ("/" + target)
                   or target.startswith(("lib/", "lib64/")))
            # Editing these on Windows can leave CRLF in the tree, which busybox
            # ash reports as "illegal option -" / "syntax error (expecting do)".
            if target.endswith((".sh", ".conf", ".txt", ".cfg", ".ini")):
                data = open(full, "rb").read()
                if b"\r\n" in data:
                    fixed = os.path.join(OUT, "build", "_lf_" + target.replace("/", "_"))
                    with open(fixed, "wb") as f:
                        f.write(data.replace(b"\r\n", b"\n"))
                    full = fixed
            arc.add_file_from(target, full, 0o755 if exe else 0o644)

    # device nodes needed before devtmpfs exists
    arc.add_device("dev/console", 5, 1, 0o600)
    arc.add_device("dev/null", 1, 3, 0o666)
    arc.add_device("dev/zero", 1, 5, 0o666)
    arc.add_device("dev/tty", 5, 0, 0o666)
    arc.add_device("dev/ptmx", 5, 2, 0o666)

    image = os.path.join(OUT, "nova-initramfs.cpio.gz")
    try:
        raw = arc.write(image, compress=True)
    except OSError as exc:
        die("cannot write %s (%s) -- close the running QEMU window first" % (image, exc))
    return image, raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-compress", action="store_true")
    ap.add_argument("--deb", action="append", default=[],
                    help="unpack a .deb into the image and register it in /apps")
    args = ap.parse_args()

    if args.deb:
        sys.path.insert(0, TOOLS)
        import import_deb

        for path in args.deb:
            import_deb.import_deb(path, os.path.join(ROOT, "rootfs"))

    zig = find_zig()
    kver = unpack_kernel()
    image, raw = build_rootfs(zig, kver)

    print()
    step("done")
    print("    kernel    : %s" % os.path.join(OUT, "nova.bzImage"))
    print("    initramfs : %s (%.1f MiB raw, %.1f MiB compressed)"
          % (image, raw / 1048576.0, os.path.getsize(image) / 1048576.0))
    print("    kernel ver: %s" % kver)


if __name__ == "__main__":
    main()
