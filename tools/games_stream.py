"""Stream the serial console so progress and errors are visible immediately."""
import os
import socket
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import QEMU, ROOT, start_vm

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
    sock = None
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", 4477), timeout=5)
            break
        except OSError:
            time.sleep(0.3)
    if not sock:
        print("no serial", flush=True)
        return 1

    def send(line):
        sock.sendall(line.encode() + b"\r")

    buf = b""
    booted = False
    start = time.time()
    step = 0
    try:
        while time.time() - start < 900:
            try:
                sock.settimeout(2.0)
                chunk = sock.recv(4096)
            except socket.timeout:
                chunk = b""
            except OSError:
                break
            if chunk:
                buf += chunk
                text = chunk.decode("utf-8", "replace")
                sys.stdout.write(text)
                sys.stdout.flush()
                if "SYSTEMUI_READY" in buf.decode("utf-8", "replace") and not booted:
                    booted = True
                    time.sleep(1)
                    send("")
                    time.sleep(1)
                    send("killall system_server; killall inputd")
                    time.sleep(1)
                    send("df -h /data | tail -n 1")
                    time.sleep(1)
                    send("wget -q -U novaos -O /tmp/probe.txt http://10.0.2.2:8899/probe.txt && cat /tmp/probe.txt || echo NET_FAIL")
            if booted and step == 0 and b"NET_" in buf[-4000:]:
                step = 1
                time.sleep(2)
                send("sh /system/bin/install-games.sh 2>&1 | tail -n 6; echo GAMES_DONE")
            if b"GAMES_DONE" in buf:
                break
    finally:
        try:
            sock.close()
        except Exception:
            pass
        try:
            vm.kill()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
