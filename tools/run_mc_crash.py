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
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)
    # the crash report from the previous VM is gone (tmpfs), so rerun the launch and
    # dump the report right after it fails
    con.buffer = ""
    con.send("portablemc --main-dir /data/mc start --dry 1.20.1 >/dev/null 2>&1; "
             "portablemc --main-dir /data/mc start --jvm /opt/jdk/bin/java 1.20.1 >/tmp/mc.log 2>&1; "
             "ls /data/mc/crash-reports/ | tail -n 1")
    deadline = time.time() + 600
    while time.time() < deadline:
        con.read_until("\x00never\x00", 2)
        if con.buffer.rstrip().endswith("#"):
            break
    con.buffer = ""
    con.send("head -n 25 /data/mc/crash-reports/$(ls /data/mc/crash-reports/ | tail -n 1)")
    time.sleep(4)
    con.buffer = ""
    con.send("echo CRASHEND")
    con.read_until("CRASHEND", 20)
    print(con.buffer.replace("\r", "")[:2500])
finally:
    p.kill()
