"""Teach build.py about the Alpine kernel (the one that ships virtio-gpu)."""
import os

root = r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova"
p = os.path.join(root, "build.py")
s = open(p, encoding="utf-8").read()

alpine_list = '''MODULES_ALPINE = [
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

'''

# insert the alpine table right before the Debian one
anchor = "MODULES = ["
i = s.find(anchor)
if "MODULES_ALPINE" not in s:
    s = s[:i] + alpine_list + s[i:]
    s = s.replace("MODULES = [", "MODULES_DEBIAN = [", 1)

# select the table by kernel flavour
if "KERNEL_KIND" not in s:
    marker = "]\n\n# Installed applications"
    s = s.replace(marker, "]\n\n# NovaOS boots the Debian kernel by default; NOVA_KERNEL=alpine picks the\n# Alpine one, which is the only one with a virtio-gpu driver (3D via virgl).\nKERNEL_KIND = os.environ.get(\"NOVA_KERNEL\", \"debian\")\nMODULES = MODULES_ALPINE if KERNEL_KIND == \"alpine\" else MODULES_DEBIAN\n\n# Installed applications", 1)

# alpine branch in unpack_kernel
if "alpine kernel" not in s:
    old = '''def unpack_kernel():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(DEB):'''
    new = '''def unpack_kernel():
    os.makedirs(OUT, exist_ok=True)
    if KERNEL_KIND == "alpine":
        return unpack_alpine_kernel()
    if not os.path.exists(DEB):'''
    s = s.replace(old, new, 1)

    helper = '''def unpack_alpine_kernel():
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


def unpack_kernel():'''
    s = s.replace("def unpack_kernel():", helper, 1)

# write /etc/modules into the image
if '"etc/modules"' not in s:
    anchor = '    arc.add_symlink("sbin/init", "/init")'
    s = s.replace(anchor, '    arc.add_file("etc/modules", "\\n".join(MODULES) + "\\n", 0o644)\n' + anchor, 1)

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("build.py patched:", "MODULES_ALPINE" in s, "unpack_alpine_kernel" in s, "etc/modules" in s)
