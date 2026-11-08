"""Install the games in NovaOS and pull the log back over a reverse netcat."""
import os
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qmp import start_vm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
LOG = os.path.join(OUT, "games.log")


def listen(port=8898):
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    srv.settimeout(1200)
    conn, _ = srv.accept()
    data = b""
    conn.settimeout(60)
    while True:
        try:
            chunk = conn.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        data += chunk
    open(LOG, "wb").write(data)
    conn.close()
    srv.close()


def main():
    threading.Thread(target=listen, daemon=True).start()
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
    sent = False
    try:
        while time.time() - start < 1200:
            try:
                sock.settimeout(2.0)
                chunk = sock.recv(4096)
            except socket.timeout:
                chunk = b""
            except OSError:
                break
            if chunk:
                buf += chunk
            if b"SYSTEMUI_READY" in buf and not sent:
                sent = True
                time.sleep(2)
                sock.sendall(b"\r")
                time.sleep(1)
                cmd = ("sh /system/bin/install-games.sh core > /tmp/g.log 2>&1; "
                       "echo RC=$? >> /tmp/g.log; sync; "
                       "nc 10.0.2.2 8898 < /tmp/g.log")
                sock.sendall(cmd.encode() + b"\r")
                print("install started", flush=True)
            if os.path.exists(LOG) and os.path.getsize(LOG) > 0:
                break
            time.sleep(1)
    finally:
        time.sleep(3)
        try:
            sock.close()
        except Exception:
            pass
        try:
            vm.kill()
        except Exception:
            pass
    if os.path.exists(LOG):
        print(open(LOG, "r", encoding="utf-8", errors="replace").read(), flush=True)
    else:
        print("no log received", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
