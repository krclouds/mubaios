import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QMP, start_vm
from serial import Console, connect
from PIL import Image

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2")
QEMU_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "tinylinux", "out", "toolchain", "msys64", "ucrt64", "bin",
                        "qemu-img.exe")


def make_disk():
    if not os.path.exists(DISK):
        subprocess.check_call([QEMU_IMG, "create", "-f", "qcow2", DISK, "4G"])


make_disk()
EXTRA = ("-m", "2048", "-append",
         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK.replace("\\", "/"),
         "-device", "virtio-blk-pci,drive=d0")

p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    con.buffer = ""
    con.send("sh /system/bin/install-x11.sh")
    t0 = time.time()
    deadline = t0 + 2400
    while time.time() < deadline:
        con.read_until("\x00never\x00", 5)
        if con.buffer.rstrip().endswith("#"):
            break
    print("=== install (%.0fs) ===" % (time.time() - t0))
    print(con.buffer.replace("\r", "")[-1500:])

    con.buffer = ""
    con.send("sync; ls /data/x11/root/usr/bin/Xorg && echo X_OK")
    con.read_until(r"#\s", 30)
    print(con.buffer.replace("\r", "")[-400:])

    con.buffer = ""
    con.send("sh /system/bin/start-x.sh >/tmp/x.log 2>&1 & sleep 12; cat /tmp/x.log | tail -n 15; echo; ps | grep Xorg | head -n 3; echo XEND")
    con.read_until("XEND", 90)
    print("=== start-x ===")
    print(con.buffer.replace("\r", "")[-1500:])

    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "xorg.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))
    print("screenshot", shot)

    con.buffer = ""
    con.send("poweroff")
    time.sleep(3)
finally:
    p.kill()
