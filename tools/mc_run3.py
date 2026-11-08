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


def ask(con, cmd, timeout=120):
    tag = "MARK%d" % next(_seq)
    con.buffer = ""
    con.send("echo")
    con.send(cmd + "; printf 'M%%s\\n' '%s'" % tag[4:])
    ok = con.read_until(tag, timeout)
    text = con.buffer.replace("\r", "")
    if not ok:
        print("[timeout]", tag, text[-400:], flush=True)
    return text


p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 240)
    con.read_until(r"#\s", 30)
    print(ask(con, "ls /data/x11/.installed | head -n1; du -sm /data/x11", 60)[-300:], flush=True)

    print(ask(con, "sm=/system/bin/start-x.sh; (sh $sm >/tmp/x.log 2>&1 &); sleep 5; echo started", 60)[-300:], flush=True)

    print("=== download ===", flush=True)
    con.buffer = ""
    con.send("(portablemc --main-dir /data/mc start --dry 1.20.1 >/data/dl.log 2>&1; echo DONE >/data/dl.flag) &")
    t0 = time.time()
    while time.time() - t0 < 1800:
        time.sleep(25)
        out = ask(con, "tail -n 1 /data/dl.log | tr '\\r' '\\n' | tail -n 1", 40)
        line = out.replace("echo", "").strip().splitlines()
        print("[dl]", line[-1][:160] if line else "", flush=True)
        if os.path.exists(os.path.join(ROOT, "out", "never")):
            break
        flag = ask(con, "ls /data/dl.flag 2>/dev/null", 30)
        if "/data/dl.flag" in flag:
            print("[dl] finished", flush=True)
            break

    print("=== launch ===", flush=True)
    con.buffer = ""
    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")
    time.sleep(90)

    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "mc3.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))

    print(ask(con, "tail -n 25 /data/mc.log", 60)[-3000:], flush=True)

    con.buffer = ""
    con.send("sync; poweroff")
    time.sleep(12)
finally:
    p.kill()
