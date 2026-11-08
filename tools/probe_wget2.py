import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")
EXTRA = ("-m", "2048", "-append", "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
         "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
         "-device", "virtio-blk-pci,drive=d0")

P = "pool/main/x/xkeyboard-config/xkb-data_2.42-1_all.deb"
URLS = [
    "http://mirrors.tuna.tsinghua.edu.cn/debian/" + P,
    "http://mirrors.aliyun.com/debian/" + P,
    "http://ftp.debian.org/debian/" + P,
    "http://deb.debian.org/debian/" + P,
]

p = start_vm(extra_args=EXTRA, serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)
    con.buffer = ""
    con.send("wget --help 2>&1 | head -n 20")
    con.read_until(r"#\s", 10)
    print(con.buffer.replace("\r", "")[:900])

    for i, url in enumerate(URLS):
        con.buffer = ""
        con.send("rm -f /tmp/u%d; wget -O /tmp/u%d '%s' 2>&1 | tail -n 3; echo RC=$?; ls -l /tmp/u%d 2>/dev/null; echo F%d" % (i, i, url, i, i))
        con.read_until("F%d" % i, 60)
        print("$", url)
        print(con.buffer.replace("\r", "")[-500:])
finally:
    p.kill()
