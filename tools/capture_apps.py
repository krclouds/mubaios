import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from PIL import Image
from qmp import QMP, start_vm
from serial import Console, connect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

SLOTS = [
    ("clock", 390, 240), ("calc", 744, 240), ("snake", 1156, 240),
    ("calendar", 390, 360), ("weather", 744, 360), ("gallery", 1156, 360),
    ("music", 390, 480), ("notes", 744, 480), ("minesweeper", 1156, 480),
    ("game2048", 390, 600), ("stopwatch", 744, 600), ("sysmon", 1156, 600),
    ("compass", 390, 720), ("about", 744, 720),
]


def main():
    p = start_vm(extra_args=("-append", "console=ttyS0 rdinit=/init loglevel=4 "
                             "vt.global_cursor_default=0 nova.debug=1"), serial="tcp")
    con = Console(connect())
    q = QMP(device=None)
    try:
        con.read_until("SYSTEMUI_READY", 150)
        con.read_until(r"#\s", 30)

        def tap(x, y, wait=1.4):
            con.buffer = ""
            con.send("input tap %d %d" % (x, y))
            con.read_until(r"#\s", 10)
            time.sleep(wait)

        def shot(name):
            path = os.path.join(OUT, name + ".ppm")
            q.screendump(path)
            time.sleep(0.6)
            Image.open(path).save(path.replace(".ppm", ".png"))
            os.remove(path)
            print("shot", name, flush=True)

        tap(346, 504, 2.2)  # store
        for app, x, y in SLOTS:
            tap(x, y, 1.4)   # install
            tap(x, y, 2.6)   # open
            shot("app-" + app)
            tap(56, 96, 1.6)  # back into the store
        print("done", flush=True)
    finally:
        p.kill()


if __name__ == "__main__":
    main()
