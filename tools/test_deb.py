import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from qmp import start_vm
from serial import Console, connect

CMD = ("sh /system/bin/debinstall.sh /samples/hello.deb >/tmp/a 2>&1; "
       "/apps/hello/hello >/tmp/b 2>&1; echo RC=$? >>/tmp/b; "
       "cat /tmp/a; echo ---; cat /tmp/b")

p = start_vm(extra_args=("-append", "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1"), serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 90)
    con.read_until(r"#\s", 30)
    con.buffer = ""
    con.send(CMD)
    time.sleep(8)
    con.buffer = ""
    con.send("echo MARKER_42")
    con.read_until("MARKER_42", 20)
    print(con.buffer.replace("\r", ""))
finally:
    p.kill()
