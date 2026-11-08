"""Install Wine in NovaOS, pull the Mini World folder over HTTP, try to launch it."""
import os
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import start_vm
from serial import Console, connect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
TAR = os.path.join(OUT, "miniworld.tar.gz")


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = lambda *a, **kw: Quiet(*a, directory=OUT, **kw)
    httpd = ThreadingHTTPServer(("0.0.0.0", 8899), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    if not os.path.exists(TAR):
        print("missing", TAR, flush=True)
        return 1
    httpd = serve()
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
    try:
        con.read_until("SYSTEMUI_READY", 240)
        try:
            con.read_until(r"#\s", 60)
        except Exception:
            con.send("")
            time.sleep(1)
        print("booted", flush=True)

        seq = [0]

        def ask(cmd, tag, timeout=1200):
            seq[0] += 1
            num = "%d" % (seq[0] * 7919)
            con.buffer = ""
            con.send(cmd + "; printf 'M%%s\\n' " + num)
            try:
                con.read_until("M" + num, timeout)
            except Exception as exc:
                print("timeout on", tag, exc, flush=True)
            return con.transcript

        con.send("killall system_server; killall inputd")
        time.sleep(1)
        ask("df -h /data | tail -n 1", "DFOK", 30)
        ask("sh /system/bin/install-wine.sh 2>&1 | tail -n 5", "WINE1", 1800)
        ask("mkdir -p /data/game && wget -q -U novaos -O - http://10.0.2.2:8899/miniworld.tar.gz | tar xz -C /data/game",
            "GAME1", 2400)
        ask("ls /data/game | head -n 5", "LSOK", 30)
        ask("sh /system/bin/start-x.sh; sleep 4; ls /tmp/.X11-unix", "XOK", 300)
        ask("cd /data/game && sh /system/bin/wine-run.sh iworldpc.exe >/tmp/wine.log 2>&1 &", "WINE2", 60)
        time.sleep(120)
        ask("tail -n 15 /tmp/wine.log", "WLOG", 60)
        print("keep-alive 25 min", flush=True)
        time.sleep(1500)
    finally:
        try:
            vm.kill()
        except Exception:
            pass
        httpd.shutdown()


if __name__ == "__main__":
    sys.exit(main())
