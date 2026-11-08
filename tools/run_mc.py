import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

p = start_vm(extra_args=("-m", "2048", "-append",
                         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
                         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0"),
             serial="tcp")


def run(con, cmd, seconds, label):
    con.buffer = ""
    con.send(cmd)
    deadline = time.time() + seconds
    while time.time() < deadline:
        con.read_until("\x00never\x00", 2)
        if con.buffer.rstrip().endswith("#"):
            break
    text = con.buffer.replace("\r", "")
    print("=== %s ===" % label)
    print(text[-2500:])
    return text


try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)

    run(con, "df -h /data | tail -n 1", 5, "df")
    run(con, "portablemc --main-dir /data/mc start --dry 1.20.1", 420, "install 1.20.1")
    run(con, "du -sh /data/mc", 5, "size")
    run(con, "portablemc --main-dir /data/mc start --jvm /opt/jdk/bin/java 1.20.1", 90, "launch")
finally:
    p.kill()
