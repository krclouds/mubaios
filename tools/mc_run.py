import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QMP, start_vm
from serial import Console, connect
from PIL import Image

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")
EXTRA = ("-m", "2048", "-append",
         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
         "-device", "virtio-blk-pci,drive=d0")

ENV = ("export LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib;"
       "export LIBGL_DRIVERS_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu/dri;"
       "export LIBGL_ALWAYS_SOFTWARE=1; export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe;"
       "export DISPLAY=:0;")


def run(con, cmd, end, timeout=600, show=1500):
    con.buffer = ""
    con.send(cmd)
    con.read_until(end, timeout)
    text = con.buffer.replace("\r", "")
    print(text[-show:])
    return text


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    print("=== extras ===")
    run(con, "sh /system/bin/install-x11.sh; echo EXDONE", "EXDONE", 300, 600)

    print("=== xorg ===")
    run(con, "sm=/system/bin/start-x.sh; sh $sm >/tmp/x.log 2>&1 & sleep 8; grep -c 'Server terminated' /data/x11/xorg.log; echo XDONE", "XDONE", 90, 600)

    print("=== download 1.20.1 ===")
    run(con, "portablemc --main-dir /data/mc --dry 1.20.1 2>&1 | tail -n 5; echo DLDONE", "DLDONE", 1200, 800)

    print("=== launch ===")
    con.buffer = ""
    con.send(ENV + " portablemc --main-dir /data/mc --jvm /opt/jdk/bin/java start 1.20.1 >/tmp/mc.log 2>&1 &")
    time.sleep(60)
    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "mc.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))

    run(con, "tail -n 40 /tmp/mc.log; echo MCDONE", "MCDONE", 60, 3000)

    run(con, "sync; poweroff", "nope", 10)
    time.sleep(4)
finally:
    p.kill()
