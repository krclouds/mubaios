import sys

sys.path.insert(0, r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova\tools")
from qmp import start_vm
from serial import Console, connect

# marker is assembled at runtime so the echoed command never contains it
CMD = "dd if=/dev/zero of=/tmp/b bs=1M count=64 2>&1 | tail -n 1; printf '%s\\n' BE''ND"

for name, extra in (("default", ()), ("host", ("-cpu", "host"))):
    p = start_vm(
        extra_args=extra
        + ("-append", "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1"),
        serial="tcp",
    )
    try:
        con = Console(connect())
        con.read_until("SYSTEMUI_READY", 150)
        con.read_until(r"#\s", 30)
        con.buffer = ""
        con.send(CMD)
        con.read_until("BEND", 200)
        out = [l for l in con.transcript.splitlines() if "copied" in l or "MB/s" in l]
        print(name, out[-2:] if out else "no dd output")
    finally:
        p.kill()
