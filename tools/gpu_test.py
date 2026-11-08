"""Boot NovaOS with virtio-gpu (virgl) and report what the guest sees."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import QMP, start_vm
from serial import Console, connect
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISK = os.path.join(ROOT, "out", "nova-disk.qcow2").replace("\\", "/")


def ask(con, cmd, expect, timeout=60):
    seq = str(int(time.time() * 1000))[-6:]
    con.buffer = ""
    con.send(cmd + "; printf '%s\\n' 'K%s'" % ("%s", seq))
    try:
        con.read_until("K" + seq, timeout)
    except Exception as exc:  # noqa: BLE001
        print("[timeout] %s (%s)" % (cmd, exc))
    out = [l for l in con.transcript.splitlines() if l.strip() and "printf" not in l]
    return "\n".join(out[-expect:])


def main():
    p = start_vm(
        extra_args=(
            "-append",
            "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1",
            "-display", "sdl,gl=on",
            "-device", "virtio-vga-gl", "-vga", "none",
            "-drive", "file=%s,if=none,id=d0,format=qcow2" % DISK,
            "-device", "virtio-blk-pci,drive=d0",
            "-m", "2560",
            "-smp", "4",
        ),
        serial="tcp",
    )
    try:
        con = Console(connect(timeout=60))
        con.read_until("SYSTEMUI_READY", 180)
        con.read_until(r"#\s", 30)
        q = QMP(device=None)
        time.sleep(1.0)
        path = os.path.join(ROOT, "out", "gpu-boot.ppm")
        q.screendump(path)
        time.sleep(0.4)
        Image.open(path).save(path.replace(".ppm", ".png"))
        print(ask(con, "ls /dev/dri; ls /sys/class/drm; cat /sys/class/drm/card0/device/uevent | head -4", 12))
        print(ask(con, "dmesg | grep -i -E 'virtio-gpu|drm|fb0' | tail -n 12", 14))
        print("ok", flush=True)
    finally:
        p.kill()


if __name__ == "__main__":
    main()
