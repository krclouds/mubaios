import itertools
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
time.sleep(2)

_seq = itertools.count()


def ask(con, cmd, timeout=120):
    tag = "MARK%d" % next(_seq)
    con.buffer = ""
    con.send(cmd + "; printf 'M%%s\\n' 'ARK%d'" % next(_seq))
    con.read_until(tag, timeout)
    text = con.buffer.replace("\r", "")
    print(text[-500:], flush=True)
    return text


try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    # the desktop keeps painting the framebuffer X is about to own: stop it first
    ask(con, "killall system_server 2>/dev/null; killall inputd 2>/dev/null; sleep 1; true", 20)
    # xfonts-base carries the "cursor" font X needs to draw a pointer
    ask(con, "rm -f /data/x11/.extra; sh /system/bin/install-x11.sh 2>&1 | tail -n 3; sync", 180)
    ask(con, "(sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &); sleep 8; "
             "grep -E 'mouse:|kbd:|cursor' /data/x11/xorg.log | tail -n 12; ls /tmp/.X11-unix/", 90)

    q = QMP(device=None)
    time.sleep(1.0)
    path = os.path.join(ROOT, 'out', 'xcursor.ppm')
    q.screendump(path)
    Image.open(path).save(path.replace('.ppm', '.png'))

    con.buffer = ""
    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")

    t0 = time.time()
    n = 0
    while time.time() - t0 < 420:
        time.sleep(30)
        n += 1
        path = os.path.join(ROOT, "out", "mcw%d.ppm" % n)
        q.screendump(path)
        Image.open(path).save(path.replace(".ppm", ".png"))
        line = ask(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 2", 40)
        print("[%3ds] %s" % (time.time() - t0, line.replace("MARK", "")[-200:]), flush=True)

    print(ask(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 25", 60)[-3000:], flush=True)
finally:
    print("VM stays open:", proc.pid, flush=True)
