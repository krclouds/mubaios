import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")
EXTRA = ("-m", "2048", "-append",
         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
         "-device", "virtio-blk-pci,drive=d0")


def run(con, cmd, end, timeout=90):
    con.buffer = ""
    con.send(cmd)
    con.read_until(end, timeout)
    return con.buffer.replace("\r", "")


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    cmds = [
        "ls -l /usr/bin/xkbcomp /data/x11/root/usr/bin/xkbcomp; echo M1",
        "LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib /usr/bin/xkbcomp -version 2>&1; echo RC=$?; echo M2",
        "ls /data/x11/root/usr/share/X11/xkb | head; echo M3",
        "LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib /usr/bin/xkbcomp -R/data/x11/root/usr/share/X11/xkb -xkm - rules evdev 2>&1 | head -n 20; echo M4",
    ]
    for cmd in cmds:
        marker = cmd.rsplit("echo ", 1)[-1].strip()
        print("---", cmd[:60])
        print(run(con, cmd, marker + "\r\n" if marker else "M4", 60)[-800:])
finally:
    p.kill()
