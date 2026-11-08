#!/usr/bin/env python3
"""End-to-end UI test for NovaOS.

The guest boots into the graphical shell.  A debug shell runs on ttyS0
(nova.debug=1) and we use it to inject real touch events with the system's
`input` tool -- the same way `adb shell input tap` drives Android.  QMP is used
only for screenshots and for the physical keyboard.

Flow: home -> Settings -> About -> back -> Terminal (type `uname -a`) -> ESC
      -> Settings -> Power off (the VM must exit).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from qmp import QMP, start_vm, wait_serial  # noqa: E402
from serial import Console, connect  # noqa: E402

ICON, GAPX, GAPY, X0, Y0 = 132, 64, 84, 280, 190


def icon_center(i):
    col, row = i % 4, i // 4
    return (X0 + col * (ICON + GAPX) + ICON // 2,
            Y0 + row * (ICON + GAPY) + ICON // 2)


def shot(q, name):
    path = os.path.join(ROOT, "out", "shot-%s.ppm" % name)
    q.screendump(path)
    time.sleep(0.5)
    print("    screenshot %s" % name)
    return path


def main():
    proc = start_vm(
        extra_args=("-append", "console=ttyS0 rdinit=/init loglevel=4 nova.debug=1"),
        serial="tcp")
    ok = True
    try:
        con = Console(connect())
        if not con.read_until("SYSTEMUI_READY", timeout=90):
            print("[FAIL] system_server never became ready")
            print(con.transcript[-3000:])
            return 1
        if not con.read_until(r"#\s", timeout=60):
            print("[FAIL] no debug shell")
            return 1
        print("[ok] graphical shell + debug shell are up")

        q = QMP(device=None)
        time.sleep(0.4)
        shot(q, "home")

        def tap(x, y, wait=1.2):
            con.buffer = ""
            con.send("input tap %d %d" % (x, y))
            con.read_until(r"#\s", timeout=15)
            time.sleep(wait)

        x, y = icon_center(0)
        tap(x, y)
        shot(q, "settings")

        tap(640, 220)
        shot(q, "settings-about")

        tap(56, 96)
        tap(56, 96)
        shot(q, "home-again")

        x, y = icon_center(1)
        tap(x, y)
        shot(q, "files")
        tap(56, 96)

        x, y = icon_center(2)
        tap(x, y)
        con.buffer = ""
        con.send("input swipe 300 400 900 550")
        con.read_until(r"#\s", timeout=15)
        time.sleep(0.8)
        shot(q, "paint")
        tap(56, 96)

        x, y = icon_center(3)
        tap(x, y)
        q.type_text("uname -a")
        q.key("ret")
        time.sleep(1.2)
        shot(q, "terminal")

        q.key("esc")
        time.sleep(1.0)
        shot(q, "home-after-terminal")

        x, y = icon_center(0)
        tap(x, y)
        tap(640, 526, wait=0.5)

        for _ in range(30):
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        exited = proc.poll() is not None
        print("[%s] power off from the Settings app" % ("ok" if exited else "FAIL"))
        ok = ok and exited
    finally:
        if proc.poll() is None:
            proc.kill()

    print("[%s] NovaOS UI test" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
