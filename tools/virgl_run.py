"""Boot with virtio-gpu (virgl) and try to bring up Xorg with the modesetting driver.

Prints what the guest sees: the DRI drivers shipped with Mesa, the X log tail and
glxinfo's renderer line.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serial import Console, connect
from qmp import start_vm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")

XORGCONF = """cat > /tmp/xvirtio.conf <<'EOF'
Section "Device"
    Identifier "gpu"
    Driver "modesetting"
    Option "AccelMethod" "glamor"
EndSection
Section "Screen"
    Identifier "screen"
    Device "gpu"
    DefaultDepth 24
EndSection
Section "ServerLayout"
    Identifier "layout"
    Screen 0 "screen"
EndSection
EOF
"""


def run(con, cmd, timeout=120):
    """Send a command, wait for a marker no echo can contain, return recent output."""
    mark = "K%06d" % (int(time.time() * 1000) % 1000000)
    con.buffer = ""
    con.send(cmd + "; printf 'K%%06d\\n' %d" % (int(mark[1:])))
    try:
        con.read_until(mark, timeout)
    except Exception as exc:  # noqa: BLE001
        print("[timeout] %s (%s)" % (cmd[:50], exc))
    text = con.transcript or ""
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines[-16:])


def main():
    p = start_vm(
        extra_args=(
            "-append",
            "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1",
            "-display", "sdl,gl=on",
            "-device", "virtio-vga-gl", "-vga", "none",
            "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
            "-device", "virtio-blk-pci,drive=d0",
            "-m", "2560", "-smp", "4",
        ),
        serial="tcp",
    )
    try:
        con = Console(connect(timeout=60))
        con.read_until("SYSTEMUI_READY", 180)
        con.read_until(r"#\s", 30)
        print("== DRI drivers ==")
        print(run(con, "ls /data/x11/root/usr/lib/x86_64-linux-gnu/dri"))
        print("== stop desktop ==")
        print(run(con, "killall system_server; killall inputd; sleep 1"))
        con.send(XORGCONF)
        time.sleep(1.0)
        env = (
            "export LD_LIBRARY_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu:/data/x11/root/usr/lib; "
            "export LIBGL_DRIVERS_PATH=/data/x11/root/usr/lib/x86_64-linux-gnu/dri; "
            "unset LIBGL_ALWAYS_SOFTWARE; unset MESA_LOADER_DRIVER_OVERRIDE; "
            "export XKB_CONFIG_ROOT=/data/x11/root/usr/share/X11/xkb; "
        )
        print("== start X (modesetting) ==")
        print(run(con, env + "(/data/x11/root/usr/lib/xorg/Xorg :0 -noreset -nolisten tcp "
                            "-modulepath /data/x11/root/usr/lib/xorg/modules "
                            "-config /tmp/xvirtio.conf -xkbdir /data/x11/root/usr/share/X11/xkb "
                            "-logfile /tmp/xv.log &); sleep 12; ls /tmp/.X11-unix; "
                            "grep -E 'glamor|virgl|modeset|\(EE\)|glx' /tmp/xv.log | tail -n 10", 90))
        print("== glxinfo ==")
        print(run(con, "DISPLAY=:0 glxinfo -B 2>&1 | head -n 12", 90))
        print("ok", flush=True)
    finally:
        p.kill()


if __name__ == "__main__":
    main()
