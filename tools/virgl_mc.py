"""Boot the virtio-gpu build, start X with virgl and launch Minecraft.

Nothing here captures the framebuffer: with `gl=on` QEMU has no 2D surface for
screendump, so the check is the X log, glxinfo/Minecraft logs and the window.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serial import Console, connect
from qmp import start_vm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")


def run(con, cmd, timeout=120, tail=14):
    mark = "K%06d" % (int(time.time() * 1000) % 1000000)
    con.buffer = ""
    con.send(cmd + "; printf 'K%%06d\\n' %d" % (int(mark[1:])))
    try:
        con.read_until(mark, timeout)
    except Exception as exc:  # noqa: BLE001
        print("[timeout] %s (%s)" % (cmd[:50], exc))
    text = con.transcript or ""
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines[-tail:])


def main():
    p = start_vm(
        extra_args=(
            "-append",
            "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1",
            "-display", "sdl,gl=on",
            "-device", "virtio-vga-gl", "-vga", "none",
            "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
            "-device", "virtio-blk-pci,drive=d0",
            "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
            "-m", "2560", "-smp", "4",
        ),
        serial="tcp",
    )
    try:
        con = Console(connect(timeout=60))
        con.read_until("SYSTEMUI_READY", 180)
        con.read_until(r"#\s", 30)
        print("== start-x ==")
        print(run(con, "sh /system/bin/start-x.sh >/tmp/sx.out 2>&1 & sleep 12; ls /tmp/.X11-unix; "
                       "grep -E 'gpu=|glamor|virgl|modeset|FBDEV' /tmp/xorg.log | tail -n 8", 90))
        print("== start mc ==")
        con.send("sh /system/bin/minecraft.sh >/tmp/mc.out 2>&1 &")
        time.sleep(150)
        print(run(con, "tr '\\r' '\\n' < /data/mc.log | grep -v Downloading | tail -n 6", 60))
        print(run(con, "ps | grep -E 'Xorg|java' | head -n 4", 60))
        print("ok", flush=True)
        print("VM stays up for an hour", flush=True)
        time.sleep(3600)
    finally:
        p.kill()


if __name__ == "__main__":
    main()
