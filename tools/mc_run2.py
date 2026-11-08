import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QMP, start_vm
from serial import Console, connect
from PIL import Image

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")
EXTRA = ("-m", "2560", "-smp", "4", "-cpu", "host", "-append",
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
    print(text[-show:], flush=True)
    return text


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    run(con, "ls /data/x11/.installed /data/x11/.extra; du -sm /data/x11; ls /data/mc | head; echo CHK", "CHK", 120, 600)

    run(con, "sm=/system/bin/start-x.sh; sh $sm >/tmp/x.log 2>&1 & sleep 6; echo XUP", "XUP", 60, 400)

    print("=== download ===", flush=True)
    run(con, "portablemc --main-dir /data/mc start --dry 1.20.1 >/data/mc-dl.log 2>&1; tail -n 3 /data/mc-dl.log; echo DLDONE", "DLDONE", 1800, 600)

    print("=== launch ===", flush=True)
    con.buffer = ""
    con.send(ENV + " portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &")
    time.sleep(75)
    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "mc2.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))

    run(con, "tail -n 30 /data/mc.log; echo MCDONE", "MCDONE", 60, 3000)

    con.buffer = ""
    con.send("sync; poweroff")
    time.sleep(12)
finally:
    p.kill()
