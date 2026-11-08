"""mc_click.py -- boot with the data disk, start X + Minecraft, then click the
menu from the host with QMP to prove the pointer path works end to end.

The VM runs with a PS/2 mouse only (no USB tablet): QMP relative events reach the
guest, and X keeps its pointer wherever the events leave it.
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

seq = [0]


def ask(con, cmd, timeout=120):
    seq[0] += 1
    tag = "K%dx" % seq[0]
    con.buffer = ""
    con.send(cmd + "; printf 'K%%s\\n' '%dx'" % seq[0])
    con.read_until(tag, timeout)
    out = con.buffer.replace("\r", "")
    print(out[-500:], flush=True)
    return out


def shot(q, name):
    path = os.path.join(ROOT, "out", name + ".ppm")
    q.screendump(path)
    Image.open(path).save(path.replace(".ppm", ".png"))


def rel(q, dx, dy):
    q.cmd("input-send-event", events=[
        {"type": "rel", "data": {"axis": "x", "value": dx}},
        {"type": "rel", "data": {"axis": "y", "value": dy}},
    ])


def click(q):
    q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}])
    time.sleep(0.15)
    q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])


try:
    con = Console(connect(timeout=90))
    con.read_until("SYSTEMUI_READY", 300)
    con.read_until(r"#\s", 60)
    ask(con, "killall system_server; killall inputd; sleep 1; (sh /system/bin/start-x.sh >/tmp/xo 2>&1 &); sleep 12; echo XOK", 120)

    q = QMP(device=None)
    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")

    t0 = time.time()
    shot_n = 0
    while time.time() - t0 < 300:
        time.sleep(40)
        shot_n += 1
        shot(q, "click-%d" % shot_n)
        tail = ask(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 1", 40)
        print("[%3ds] %s" % (time.time() - t0, tail.strip().splitlines()[-1][-140:]), flush=True)

    # pointer to the middle of the window, then click "Singleplayer"
    rel(q, 0, 0)
    time.sleep(0.5)
    click(q)
    time.sleep(20)
    shot(q, "click-single")
    print("[click] done", flush=True)
finally:
    print("[vm] left running", proc.pid, flush=True)
