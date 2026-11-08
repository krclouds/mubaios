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


def run(con, cmd, end, timeout=120):
    con.buffer = ""
    con.send(cmd)
    con.read_until(end, timeout)
    return con.buffer.replace("\r", "")


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    out = run(con, "printf 'M%s\\n' 'ARK1'; ls -l /data/x11/root/usr/bin/Xorg; printf 'M%s\\n' 'ARK2'", "MARK2", 60)
    print("[A]", out[-600:])

    out = run(con, "sh /system/bin/start-x.sh >/tmp/x.log 2>&1 & sleep 20; printf 'M%s\\n' 'ARK3'; tail -n 30 /tmp/x.log; echo ---; tail -n 30 /data/x11/xorg.log; printf 'M%s\\n' 'ARK4'", "MARK4", 120)
    print("[B]", out[-4000:])

    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "xorg2.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))

    run(con, "ps | grep -i xorg | head -n 3; sync; poweroff", "never", 5)
    time.sleep(3)
finally:
    p.kill()
