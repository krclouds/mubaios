import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

CMD = "portablemc --main-dir /data/mc start --dry 1.7.10"

p = start_vm(extra_args=("-m", "2048", "-append",
                         "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1",
                         "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0"),
             serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 120)
    con.read_until(r"#\s", 30)
    con.buffer = ""
    con.send(CMD)
    deadline = time.time() + 260
    last = time.time()
    while time.time() < deadline:
        con.read_until("\x00never\x00", 2)
        if con.buffer.rstrip().endswith("#"):
            break
        if time.time() - last > 20:
            last = time.time()
            tail = con.buffer.replace("\r", "").strip().splitlines()[-1:] or [""]
            print("...", tail[0][-120:], flush=True)
    text = con.buffer.replace("\r", "")
    print("=== tail ===")
    print(text[-3000:])
finally:
    p.kill()
