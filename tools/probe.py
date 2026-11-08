#!/usr/bin/env python3
"""Boot NovaOS and ask the guest whether the framebuffer and input devices exist."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from serial import Console, PORT, connect  # noqa: E402

QEMU = os.path.join(os.path.dirname(ROOT), "tinylinux", "out", "toolchain", "msys64",
                    "ucrt64", "bin", "qemu-system-x86_64.exe")

COMMANDS = [
    ("framebuffer", "cat /proc/fb"),
    ("fb geometry", "ls -l /dev/fb0; cat /sys/class/graphics/fb0/virtual_size 2>/dev/null"),
    ("input nodes", "ls -l /dev/input"),
    ("input devices", "cat /proc/bus/input/devices"),
    ("uname", "uname -r"),
]


def main():
    proc = subprocess.Popen([
        QEMU, "-m", "512", "-smp", "2",
        "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
        "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
        "-append", "console=ttyS0 rdinit=/init loglevel=4 nova.shell=1",
        "-vga", "std", "-usb", "-device", "usb-tablet",
        "-display", "none", "-monitor", "none",
        "-serial", "tcp:127.0.0.1:%d,server=on,wait=on" % PORT,
        "-net", "none", "-no-reboot",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    try:
        con = Console(connect())
        if not con.read_until(r"#\s", timeout=120):
            print("no shell prompt; serial output:")
            print(con.transcript)
            return 1
        for label, cmd in COMMANDS:
            con.buffer = ""
            con.send(cmd)
            con.read_until(r"/#\s", timeout=25)
            print("\n===== %s =====" % label)
            print(con.buffer.replace("\r", ""))
        con.send("poweroff")
        return 0
    finally:
        proc.kill()


if __name__ == "__main__":
    sys.exit(main())
