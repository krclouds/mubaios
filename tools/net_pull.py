"""Serial is lossy for long output, so the guest pushes files to the host over
QEMU's user-mode network: guest -> 10.0.2.2:<port> lands on this listener.

usage: python tools/net_pull.py <guest-path> [out-name]
"""
import os
import socket
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import QEMU
from serial import Console, connect

guest_path = sys.argv[1] if len(sys.argv) > 1 else "/data/x11/xorg.log"
out_name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(guest_path)
PORT = 8899
DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", PORT))
srv.listen(1)
srv.settimeout(180)

args = [
    QEMU, "-m", "1024", "-smp", "2", "-accel", "whpx",
    "-kernel", os.path.join(ROOT, "out", "nova.bzImage"),
    "-initrd", os.path.join(ROOT, "out", "nova-initramfs.cpio.gz"),
    "-append", "console=ttyS0 rdinit=/init loglevel=3 vt.global_cursor_default=0 nova.debug=1",
    "-vga", "std",
    "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
    "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
    "-device", "virtio-blk-pci,drive=d0",
    "-display", "none", "-serial", "tcp:127.0.0.1:4477,server=on,wait=off", "-no-reboot",
]
import subprocess

proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    con = Console(connect(timeout=90))
    con.read_until("SYSTEMUI_READY", 300)
    con.read_until(r"#\s", 60)
    con.buffer = ""
    con.send("cat %s | nc 10.0.2.2 %d; echo SENT" % (guest_path, PORT))
    data = bytearray()
    srv.settimeout(120)
    conn, addr = srv.accept()
    conn.settimeout(5)
    while True:
        try:
            chunk = conn.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        data += chunk
    conn.close()
    out = os.path.join(ROOT, "out", out_name)
    with open(out, "wb") as f:
        f.write(data)
    print("saved", out, len(data), "bytes", flush=True)
finally:
    proc.kill()
