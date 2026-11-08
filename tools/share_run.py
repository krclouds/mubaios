"""Boot NovaOS with a 9p host share, run a script from it, report its log."""
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import start_vm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
SHARE = os.path.join(OUT, "share")


def main():
    script = sys.argv[1] if len(sys.argv) > 1 else "run.sh"
    log = os.path.join(SHARE, "log.txt")
    if os.path.exists(log):
        os.remove(log)
    vm = start_vm(
        extra_args=(
            "-device", "virtio-vga-gl", "-vga", "none",
            "-display", "sdl,gl=on",
            "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
            "-m", "2560", "-smp", "4",
            "-drive", "file=%s,if=none,id=d0,format=qcow2" % os.path.join(OUT, "nova-disk.qcow2"),
            "-device", "virtio-blk-pci,drive=d0",
            "-virtfs", "local,path=%s,mount_tag=hostshare,security_model=none" % SHARE,
        ),
        serial="tcp",
    )
    sock = None
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", 4477), timeout=5)
            break
        except OSError:
            time.sleep(0.3)
    if not sock:
        print("no serial", flush=True)
        return 1
    buf = b""
    start = time.time()
    booted = False
    sent = False
    try:
        while time.time() - start < 1500:
            try:
                sock.settimeout(2.0)
                chunk = sock.recv(4096)
            except socket.timeout:
                chunk = b""
            except OSError:
                break
            if chunk:
                buf += chunk
                if b"SYSTEMUI_READY" in buf and not booted:
                    booted = True
                    time.sleep(2)
                    sock.sendall(b"\r")
                    time.sleep(1)
                    sock.sendall(("sh /mnt/host/%s" % script).encode() + b"\r")
                    sent = True
                    print("script sent", flush=True)
            if sent and os.path.exists(log):
                data = open(log, "r", encoding="utf-8", errors="replace").read()
                if "GAMES_DONE" in data:
                    print(data, flush=True)
                    break
            time.sleep(1)
    finally:
        try:
            sock.close()
        except Exception:
            pass
        try:
            vm.kill()
        except Exception:
            pass
    if os.path.exists(log):
        print("---- log ----", flush=True)
        print(open(log, "r", encoding="utf-8", errors="replace").read(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
