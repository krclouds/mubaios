"""Unpack the Alpine linux-lts apk into out/alpine (kernel + gunzipped modules).

The Debian kernel NovaOS ships with has no virtio-gpu driver, so the GPU path
swaps in Alpine's kernel, which does.  This tool materialises:

    out/alpine/vmlinuz-lts
    out/alpine/modules/kernel/...   (plain .ko, no /lib/modules prefix)
    out/alpine/modules/modules.dep  (dependency lines for our module list)
"""
import os
import sys
import tarfile
import gzip
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(ROOT, "out", "alpine")
APK = os.path.join(CACHE, "linux-lts.apk")

# Everything NovaOS needs at boot.  Listed in dependency order; the graph comes
# from the apk's modules.dep so we do not have to guess.
WANT = [
    "virtio", "virtio_ring", "virtio_pci_legacy_dev", "virtio_pci_modern_dev",
    "virtio_pci", "virtio_dma_buf", "drm", "drm_kms_helper",
    "drm_shmem_helper", "virtio-gpu",
    "evdev", "uinput", "psmouse", "usb-common", "usbcore", "uhci-hcd",
    "hid", "usbhid", "hid-generic",
    "failover", "net_failover", "virtio_net",
    "9p", "9pnet", "9pnet_virtio", "fscache", "netfs", "virtio_blk", "crc16", "mbcache", "jbd2", "ext4",
    "crc32c_generic", "crc32c-intel", "fb", "cfbfillrect", "cfbimgblt",
    "cfbcopyarea", "fb_sys_fops", "syscopyarea", "sysfillrect", "sysimgblt",
]


def main():
    if not os.path.isfile(APK):
        sys.exit("missing %s" % APK)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "modules"), exist_ok=True)

    tf = tarfile.open(APK)
    names = tf.getnames()
    dep = None
    if "lib/modules" in " ".join(names):
        for n in names:
            if n.endswith("modules.dep"):
                dep = tf.extractfile(n).read().decode()
                break

    prefix = None
    for n in names:
        if n.endswith(".ko.gz"):
            prefix = n.split("/kernel/")[0]
            break
    if not prefix:
        sys.exit("no modules inside the apk")

    kept = 0
    for n in names:
        if n.endswith("boot/vmlinuz-lts"):
            with tf.extractfile(n) as src, open(os.path.join(OUT, "vmlinuz-lts"), "wb") as dst:
                shutil.copyfileobj(src, dst)
            continue
        if not n.endswith(".ko.gz"):
            continue
        stem = os.path.basename(n)[:-6]  # strip .ko.gz
        if stem not in WANT:
            continue
        rel = n[len(prefix) + 1:]
        rel = rel[:-3]  # strip .gz
        dst = os.path.join(OUT, "modules", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with tf.extractfile(n) as src:
            data = gzip.decompress(src.read())
        with open(dst, "wb") as f:
            f.write(data)
        kept += 1

    if dep:
        lines = []
        for line in dep.splitlines():
            mod = line.split(":")[0]
            if os.path.basename(mod)[:-3] in WANT:
                lines.append(line)
        with open(os.path.join(OUT, "modules", "modules.dep"), "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")

    print("alpine kernel: %d modules, %d dep lines" % (kept, len(lines) if dep else 0))


if __name__ == "__main__":
    main()
