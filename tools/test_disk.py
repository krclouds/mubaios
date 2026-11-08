import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2")
EXTRA = ("-m", "2048",
         "-append", "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK.replace("\\", "/"),
         "-device", "virtio-blk-pci,drive=d0")


def boot(con_cmds):
    p = start_vm(extra_args=EXTRA, serial="tcp")
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)
    logs = [l for l in con.transcript.splitlines() if "data disk" in l or "vda" in l]
    print("boot log:", logs[-6:])
    for cmd, wait in con_cmds:
        con.buffer = ""
        con.send(cmd)
        time.sleep(wait)
        con.send("echo Q1")
        con.read_until("Q1", 15)
        out = con.buffer.replace("\r", "")
        print("$", cmd)
        print(out[:600])
    return p


p = boot([("echo hello-from-first-boot > /data/persist.txt; sync; ls -l /data", 3)])
p.kill()
time.sleep(2)
print("---- reboot ----")
p = boot([("cat /data/persist.txt; ls /data", 3)])
p.kill()
