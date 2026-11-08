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


def wait_prompt(con, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        con.read_until("\x00never\x00", 2)
        if con.buffer.rstrip().endswith("#"):
            return True
    return False


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)

    con.buffer = ""
    con.send("sh /system/bin/install-x11.sh")
    wait_prompt(con, 900)
    text = con.buffer.replace("\r", "")
    print("=== install tail ===")
    print(text[-1200:])

    con.buffer = ""
    con.send("sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &")
    time.sleep(8)
    con.buffer = ""
    con.send("sleep 5; head -n 40 /data/x11/xorg.log 2>/dev/null; echo; ps | grep -c Xorg; echo XEND")
    wait_prompt(con, 60)
    print("=== xorg ===")
    print(con.buffer.replace("\r", "")[:2500])
finally:
    p.kill()
