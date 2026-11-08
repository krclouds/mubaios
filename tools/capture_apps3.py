import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from PIL import Image
from qmp import QMP, start_vm
from serial import Console, connect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

SLOTS = [("clock", 390, 240), ("game2048", 390, 600), ("about", 744, 720)]


def main():
    p = start_vm(extra_args=("-append", "console=ttyS0 rdinit=/init loglevel=4 "
                             "vt.global_cursor_default=0 nova.debug=1"), serial="tcp")
    con = Console(connect())
    q = QMP(device=None)
    try:
        con.read_until("SYSTEMUI_READY", 150)
        con.read_until(r"#\s", 30)

        def tap(x, y, wait=1.8):
            con.buffer = ""
            con.send("input tap %d %d" % (x, y))
            con.read_until(r"#\s", 12)
            time.sleep(wait)

        def run(cmd, wait=0.8):
            con.buffer = ""
            con.send(cmd)
            con.read_until(r"#\s", 12)
            time.sleep(wait)
            return con.transcript

        tap(346, 504, 2.4)  # store
        for app, x, y in SLOTS:
            tap(x, y, 2.0)
            out = run("ls /apps/" + app)
            print(app, "installed" if app in out.split("ls /apps/" + app)[-1] else "MISSING", flush=True)
            tap(x, y, 3.0)
            path = os.path.join(OUT, "app-" + app + ".ppm")
            q.screendump(path)
            time.sleep(0.7)
            Image.open(path).save(path.replace(".ppm", ".png"))
            os.remove(path)
            print("shot app-" + app, flush=True)
            tap(56, 96, 1.8)
        print("done", flush=True)
    finally:
        p.kill()


if __name__ == "__main__":
    main()
