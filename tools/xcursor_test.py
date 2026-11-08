"""xcursor_test.py -- boot with the data disk, start Xorg, then prove whether the
X pointer works: grep the graph's input lines out of xorg.log and move the mouse
with QMP, taking screenshots before/after.
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

args = [
    QEMU, "-m", "2048", "-smp", "4", "-cpu", "host", "-accel", "whpx",
    "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
    "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
    "-append", "console=ttyS0 rdinit=/init loglevel=3 vt.global_cursor_default=0 nova.debug=1",
    "-vga", "std",
    "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
    "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
    "-device", "virtio-blk-pci,drive=d0",
    "-display", "none",
    "-qmp", "tcp:127.0.0.1:4451,server=on,wait=off",
    "-serial", "tcp:127.0.0.1:4477,server=on,wait=off",
    "-no-reboot",
]
proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

n = [0]


def ask(con, cmd, timeout=120):
    n[0] += 1
    seq = n[0]
    tag = "Z%d|Z" % seq
    con.buffer = ""
    # the tag must not appear in the echoed command line
    con.send(cmd + "; printf 'Z%%s|%%s\\n' %d 'Z'" % seq)
    con.read_until(tag, timeout)
    text = con.buffer.replace("\r", "")
    print(text[-700:], flush=True)
    return text


def shot(q, name):
    path = os.path.join(ROOT, "out", name + ".ppm")
    q.screendump(path)
    Image.open(path).save(path.replace(".ppm", ".png"))


def rel(q, dx, dy):
    q.cmd("input-send-event", events=[
        {"type": "rel", "data": {"axis": "x", "value": dx}},
        {"type": "rel", "data": {"axis": "y", "value": dy}},
    ])


try:
    con = Console(connect(timeout=90))
    con.read_until("SYSTEMUI_READY", 300)
    con.read_until(r"#\s", 60)
    ask(con, "killall system_server 2>/dev/null; killall inputd 2>/dev/null; sleep 1; true", 30)
    ask(con, "(sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &); sleep 10; "
             "grep -iE 'Using input driver|evdev:|cursor|pointer' /data/x11/xorg.log | tail -n 30", 150)

    # dump the whole log to the host: serial echo makes the grep output unreadable
    con.buffer = ""
    con.send("cat /data/x11/xorg.log")
    time.sleep(6)
    with open(os.path.join(ROOT, "out", "xorg-dump.txt"), "w", encoding="utf-8") as f:
        f.write(con.buffer.replace("\r", ""))

    q = QMP(device=None)
    time.sleep(1)
    shot(q, "cur-a")
    for _ in range(6):
        rel(q, 40, 25)
        time.sleep(0.4)
    time.sleep(1)
    shot(q, "cur-b")
    print("[x] screenshots cur-a/cur-b", flush=True)
finally:
    print("[vm]", proc.pid, flush=True)
