import os
import sys

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

TESTS = [
    ("plain", "/usr/bin/xkbcomp -version >/tmp/o1 2>&1; echo RC=$? >>/tmp/o1; cat /tmp/o1; echo E1"),
    ("ldtrace", "LD_TRACE_LOADED_OBJECTS=1 /data/x11/root/usr/bin/xkbcomp 2>&1 | head -n 12; echo E2"),
    ("onlylib", "LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu /data/x11/root/usr/bin/xkbcomp -version >/tmp/o3 2>&1; echo RC=$? >>/tmp/o3; cat /tmp/o3; echo E3"),
]

p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)
    con.buffer = ""
    con.send("mkdir -p /usr/bin; ln -sf /data/x11/root/usr/bin/xkbcomp /usr/bin/xkbcomp; echo READY")
    con.read_until("READY", 30)
    for name, cmd in TESTS:
        con.buffer = ""
        con.send(cmd)
        end = cmd.rsplit("echo ", 1)[-1].strip()
        con.read_until(end, 60)
        print("===", name)
        print(con.buffer.replace("\r", "")[-900:])
finally:
    p.kill()
