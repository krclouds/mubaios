import sys

sys.path.insert(0, r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova\tools")
from qmp import start_vm
from serial import Console, connect

PRE = "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1"

CMDS = [
    ("cpus", "grep -c ^processor /proc/cpuinfo; printf '%s\\n' C''END"),
    ("zero", "dd if=/dev/zero of=/dev/null bs=1M count=2048 2>&1 | tail -n 1; printf '%s\\n' Z''END"),
    ("loop", "S=$(cat /proc/uptime); i=0; while [ $i -lt 200000 ]; do i=$((i+1)); done; E=$(cat /proc/uptime); echo LOOP $S $E; printf '%s\\n' L''END"),
]


def run(extra, label):
    p = start_vm(extra_args=extra + ("-append", PRE), serial="tcp")
    try:
        con = Console(connect())
        con.read_until("SYSTEMUI_READY", 150)
        con.read_until(r"#\s", 30)
        out = {}
        for name, cmd in CMDS:
            con.buffer = ""
            con.send(cmd)
            tag = {"cpus": "CEND", "zero": "ZEND", "loop": "LEND"}[name]
            con.read_until(tag, 240)
            lines = [l.strip() for l in con.transcript.splitlines() if l.strip()]
            out[name] = lines[-2:] if lines else []
        print(label, out)
    finally:
        p.kill()


run((), "whpx-4cpu")
run(("-smp", "1"), "whpx-1cpu")
