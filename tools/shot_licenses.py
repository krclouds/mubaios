"""Capture the in-system 开源许可 app (page 1 and page 2)."""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from PIL import Image  # noqa: E402
from qmp import QMP, start_vm  # noqa: E402
from serial import Console, connect  # noqa: E402

p = start_vm(extra_args=("-append", "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1"),
             serial="tcp")
try:
    con = Console(connect())
    con.read_until("SYSTEMUI_READY", 180)
    con.read_until(r"#\s", 30)
    q = QMP(device=None)

    def cmd(c, wait=2.2):
        con.buffer = ""
        con.send(c)
        con.read_until(r"#\s", 15)
        time.sleep(wait)

    def shot(name):
        path = os.path.join(ROOT, "out", name + ".ppm")
        q.screendump(path)
        time.sleep(0.6)
        Image.open(path).save(path.replace(".ppm", ".png"))
        os.remove(path)

    shot("lic-home")
    cmd("input tap 542 504", 2.6)
    shot("lic-page1")
    cmd("input tap 1180 748", 2.0)
    shot("lic-page2")
    print("done")
finally:
    p.kill()
