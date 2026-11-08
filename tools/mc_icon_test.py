import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qmp import QMP, QEMU, ROOT
from serial import PORT as SERIAL_PORT, Console, connect
from PIL import Image

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2")

args = [
    QEMU, "-m", "2560", "-smp", "4", "-accel", "whpx",
    "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
    "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
    "-append", "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1",
    "-vga", "std", "-usb", "-device", "usb-tablet",
    "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
    "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
    "-device", "virtio-blk-pci,drive=d0",
    "-display", "none",
    "-qmp", "tcp:127.0.0.1:4472,server=on,wait=off",
    "-serial", "tcp:127.0.0.1:%d,server=on,wait=off" % SERIAL_PORT,
    "-no-reboot",
]

proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
time.sleep(1.0)


def shot(name):
    path = os.path.join(ROOT, "out", name + ".ppm")
    q.cmd("screendump", filename=path)
    time.sleep(0.6)
    Image.open(path).save(path.replace(".ppm", ".png"))


try:
    con = Console(connect(SERIAL_PORT))
    con.read_until("SYSTEMUI_READY", 150)
    con.read_until(r"#\s", 30)
    q = QMP(port=4472)

    def shell(cmd, wait=r"#\s", timeout=60):
        con.buffer = ""
        con.send(cmd)
        con.read_until(wait, timeout)
        return con.buffer

    shot("mc1-home")
    shell("input tap 542 520", timeout=20)     # 我的世界 icon
    t0 = time.time()
    while time.time() - t0 < 150:
        time.sleep(10)
        try:
            out = shell("pidof system_server; uptime", timeout=20)
        except Exception as exc:
            out = "SERIAL-DEAD %s" % exc
        print("[%3ds] %s" % (time.time() - t0, out.strip().replace("\r", "")[:120]))
    shot("mc2-running")
    print("MC LOG:")
    print(shell("tail -n 3 /data/mc.log", timeout=30)[-400:])
    shell("rm -f /run/mc_mode; killall Xorg; rm -f /tmp/.X11-unix/X0", timeout=30)
    time.sleep(8)
    shot("mc3-back")
    print("still alive:", shell("pidof system_server", timeout=20).strip())
finally:
    proc.kill()
