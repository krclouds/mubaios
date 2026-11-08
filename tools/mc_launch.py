import itertools
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

_seq = itertools.count()


def ask(con, cmd, timeout=90, quiet=True):
    tag = "MARK%d" % next(_seq)
    con.buffer = ""
    con.send(cmd + "; printf 'M%%s\\n' 'ARK%d'" % next(_seq))
    ok = con.read_until(tag, timeout)
    text = con.buffer.replace("\r", "")
    if not ok and not quiet:
        print("[timeout]", tag, text[-300:], flush=True)
    return text


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)

    print(ask(con, "(sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &); sleep 8; ls /tmp/.X11-unix/; du -sm /data/mc", 90)[-400:], flush=True)

    con.buffer = ""
    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")

    q = QMP(device=None)
    t0 = time.time()
    shot_n = 0
    while time.time() - t0 < 900:
        time.sleep(45)
        shot_n += 1
        path = os.path.join(ROOT, "out", "mc-step%d.ppm" % shot_n)
        q.screendump(path)
        Image.open(path).save(path.replace(".ppm", ".png"))
        line = ask(con, "tr '\\r' '\\n' < /data/mc.log | tail -n 1", 40).strip()
        print("[%3ds] %s" % (time.time() - t0, line.splitlines()[-1][:150] if line else ""), flush=True)

    print("[log]", ask(con, "tail -n 40 /data/mc.log", 60)[-3500:], flush=True)

    con.buffer = ""
    con.send("sync; poweroff")
    try:
        p.wait(timeout=60)
    except Exception:
        pass
finally:
    if p.poll() is None:
        p.kill()
