"""mc_final.py -- boot NovaOS with the data disk, repair it if needed, start
Xorg and launch Minecraft 1.20.1 in a visible QEMU window.

Deliberately slow and forgiving: no killing mid-write, generous timeouts, and
the VM is left running at the end so the user can interact with it.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QEMU, QMP
from serial import Console, connect
from PIL import Image

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")
ENV = ("export LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib;"
       "export LIBGL_DRIVERS_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu/dri;"
       "export LIBGL_ALWAYS_SOFTWARE=1; export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe;"
       "export DISPLAY=:0;")

args = [
    QEMU, "-m", "2560", "-smp", "4", "-cpu", "host", "-accel", "whpx",
    "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
    "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
    "-append", "console=ttyS0 rdinit=/init loglevel=3 vt.global_cursor_default=0 nova.debug=1",
    "-vga", "std",
    "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
    "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
    "-device", "virtio-blk-pci,drive=d0",
    "-display", "gtk",
    "-qmp", "tcp:127.0.0.1:4451,server=on,wait=off",
    "-serial", "tcp:127.0.0.1:4477,server=on,wait=off",
    "-no-reboot",
]
proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

counter = [0]


def ask(con, cmd, timeout=120, quiet=False):
    counter[0] += 1
    tag = "M%dK" % counter[0]
    con.buffer = ""
    con.send(cmd + "; printf 'M%%s\\n' 'A%s'" % tag)
    con.read_until(tag, timeout)
    text = con.buffer.replace("\r", "")
    if not quiet:
        print(text[-600:], flush=True)
    return text


try:
    con = Console(connect(timeout=90))
    con.read_until("SYSTEMUI_READY", 300)
    con.read_until(r"#\s", 60)
    print("[boot] desktop up", flush=True)

    # Mount the data disk; if it is damaged run a repair pass first.
    ask(con, "ls /data >/dev/null 2>&1 && echo DISK_OK || echo DISK_BAD", 30)
    con.buffer = ""
    ask(con, "mountpoint -q /data && echo MOUNTED || echo NOT_MOUNTED", 30)
    if "MOUNTED" not in con.buffer:
        print("[disk] not mounted, repairing", flush=True)
        ask(con, "umount /data 2>/dev/null; fsck.ext4 -y /dev/vda 2>&1 | tail -n 5", 300)
        ask(con, "mount -t ext4 /dev/vda /data && echo REMOUNTED", 60)

    ask(con, "killall system_server 2>/dev/null; killall inputd 2>/dev/null; sleep 1; true", 30)
    ask(con, "(sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &); sleep 10; "
             "grep -E 'mouse:|kbd:|Cursor' /data/x11/xorg.log | tail -n 8; ls /tmp/.X11-unix/", 120)

    q = QMP(device=None)
    time.sleep(2)
    path = os.path.join(ROOT, "out", "x-ready.ppm")
    q.screendump(path)
    Image.open(path).save(path.replace(".ppm", ".png"))
    print("[x] screenshot written", flush=True)

    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")

    t0 = time.time()
    shot = 0
    while time.time() - t0 < 600:
        time.sleep(45)
        shot += 1
        path = os.path.join(ROOT, "out", "mc-final-%d.ppm" % shot)
        q.screendump(path)
        Image.open(path).save(path.replace(".ppm", ".png"))
        line = ask(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 1", 40, quiet=True)
        print("[%3ds] %s" % (time.time() - t0, line.strip().splitlines()[-1][-160:]), flush=True)

    print(ask(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 20", 60, quiet=True)[-2500:])
finally:
    print("[vm] left running, pid", proc.pid, flush=True)
