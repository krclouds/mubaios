import itertools
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QMP, start_vm
from serial import Console, connect
from PIL import Image

QEMU_IMG = os.path.join(ROOT, "..", "tinylinux", "out", "toolchain", "msys64",
                        "ucrt64", "bin", "qemu-img.exe")
DISK = os.path.join(ROOT, "out", "nova-disk.qcow2")

if not os.path.exists(DISK):
    subprocess.check_call([QEMU_IMG, "create", "-f", "qcow2", DISK, "4G"])

EXTRA = ("-m", "2560", "-smp", "4", "-cpu", "host", "-append",
         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK.replace("\\", "/"),
         "-device", "virtio-blk-pci,drive=d0")

ENV = ("export LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib;"
       "export LIBGL_DRIVERS_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu/dri;"
       "export LIBGL_ALWAYS_SOFTWARE=1; export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe;"
       "export DISPLAY=:0;")

_seq = itertools.count()


def ask(con, cmd, timeout=120, quiet=False):
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

    print("[state]", ask(con, "ls /data/x11/.installed 2>/dev/null; du -sm /data/x11 2>/dev/null", 60)[-200:], flush=True)

    print("=== install ===", flush=True)
    con.buffer = ""
    con.send("sh /system/bin/install-x11.sh")
    t0 = time.time()
    while time.time() - t0 < 1500:
        con.read_until("\x00never\x00", 10)
        if con.buffer.rstrip().endswith("#"):
            break
    print(con.buffer.replace("\r", "")[-600:], flush=True)

    print("=== xorg ===", flush=True)
    print(ask(con, "(sh /system/bin/start-x.sh >/tmp/x.log 2>&1 &); sleep 6; ls /tmp/.X11-unix/ 2>/dev/null", 60)[-400:], flush=True)

    print("=== download ===", flush=True)
    con.buffer = ""
    con.send("(portablemc --main-dir /data/mc start --dry 1.20.1 >/data/dl.log 2>&1; touch /data/dl.ok) &")
    time.sleep(10)
    t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(20)
        line = ask(con, "tr '\\r' '\\n' < /data/dl.log | tail -n 1", 40, quiet=True).replace("\r", "")
        last = [x for x in line.splitlines() if "M" not in x or True]
        print("[dl]", line.strip().splitlines()[-1][:140] if line.strip() else "", flush=True)
        if ask(con, "ls /data/dl.ok 2>/dev/null", 30, quiet=True).find("/data/dl.ok") >= 0:
            print("[dl] done", flush=True)
            break

    print("=== launch ===", flush=True)
    con.buffer = ""
    con.send(ENV + " (portablemc --main-dir /data/mc start 1.20.1 >/data/mc.log 2>&1 &)")
    time.sleep(100)

    q = QMP(device=None)
    shot = os.path.join(ROOT, "out", "mc4.ppm")
    q.screendump(shot)
    time.sleep(0.5)
    Image.open(shot).save(shot.replace(".ppm", ".png"))

    print("[mc]", ask(con, "tail -n 25 /data/mc.log", 60)[-2500:], flush=True)

    con.buffer = ""
    con.send("sync; poweroff")
    try:
        p.wait(timeout=60)
    except Exception:
        pass
finally:
    if p.poll() is None:
        p.kill()
