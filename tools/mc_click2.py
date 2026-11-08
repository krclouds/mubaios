"""Drive the running NovaOS VM through QMP: click into a world and press F3.

The virgl boot has no 2D surface for screendump, so the screenshot has to come
from the host desktop after this runs.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import QMP


def move(q, dx, dy, steps=8):
    for _ in range(steps):
        q.cmd("input-send-event", events=[
            {"type": "rel", "data": {"axis": "x", "value": int(dx / steps)}},
            {"type": "rel", "data": {"axis": "y", "value": int(dy / steps)}},
        ])
        time.sleep(0.02)


def click(q):
    q.cmd("input-send-event", events=[
        {"type": "btn", "data": {"down": True, "button": "left"}},
    ])
    time.sleep(0.12)
    q.cmd("input-send-event", events=[
        {"type": "btn", "data": {"down": False, "button": "left"}},
    ])


def key(q, qcode):
    q.cmd("input-send-event", events=[
        {"type": "key", "data": {"down": True, "key": {"type": "qcode", "data": qcode}}},
    ])
    time.sleep(0.08)
    q.cmd("input-send-event", events=[
        {"type": "key", "data": {"down": False, "key": {"type": "qcode", "data": qcode}}},
    ])


def main():
    q = QMP(device=None)
    q.cmd("input-send-event", events=[{"type": "rel", "data": {"axis": "x", "value": -4000}},
                                      {"type": "rel", "data": {"axis": "y", "value": -4000}}])
    time.sleep(0.5)
    move(q, 640, 655)
    time.sleep(0.4)
    click(q)          # 单人游戏
    time.sleep(4)
    move(q, 0, -120)
    time.sleep(0.4)
    click(q)          # 创建新的世界 (if the list is empty the button sits here)
    time.sleep(4)
    key(q, "ret")
    time.sleep(45)
    key(q, "f3")
    time.sleep(2)
    print("done")


if __name__ == "__main__":
    main()
