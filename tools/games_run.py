"""Install bsdgames + luanti inside NovaOS and try both."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import start_vm
from serial import Console, connect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")


def main():
    vm = start_vm(
        extra_args=(
            "-device", "virtio-vga-gl", "-vga", "none",
            "-display", "sdl,gl=on",
            "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
            "-m", "2560", "-smp", "4",
            "-drive", "file=%s,if=none,id=d0,format=qcow2" % os.path.join(OUT, "nova-disk.qcow2"),
            "-device", "virtio-blk-pci,drive=d0",
        ),
        serial="tcp",
    )
    con = Console(connect())
    seq = [0]

    def ask(cmd, timeout=600):
        seq[0] += 1
        num = "%d" % (seq[0] * 7919)
        con.buffer = ""
        con.send(cmd + "; printf 'M%s\\n' " + num)
        try:
            con.read_until("M" + num, timeout)
        except Exception as exc:
            print("timeout", num, exc, flush=True)
        tail = [l for l in con.transcript.splitlines() if l.strip()][-6:]
        print("\n".join(tail), flush=True)

    try:
        con.read_until("SYSTEMUI_READY", 240)
        time.sleep(2)
        ask("df -h /data | tail -n 1", 30)
        ask("killall system_server; killall inputd", 30)
        ask("sh /system/bin/install-games.sh 2>&1 | tail -n 4", 1800)
        ask("ls /data/games/root/usr/games | head -n 12", 30)
        # terminal game: run bsdgames' worm in the serial console briefly
        ask("LD_LIBRARY_PATH=/data/games/root/usr/lib/x86_64-linux-gnu:/data/games/root/lib/x86_64-linux-gnu "
            "/data/games/root/usr/games/worm -n 3 2>&1 | head -n 6", 60)
        ask("sh /system/bin/start-x.sh; sleep 3; ls /tmp/.X11-unix", 300)
        ask("ls /data/games/root/usr/games | grep -i -E 'luanti|minetest'", 30)
        print("keep-alive 6 min", flush=True)
        time.sleep(360)
    finally:
        try:
            vm.kill()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
