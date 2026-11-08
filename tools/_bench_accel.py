import sys

sys.path.insert(0, r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova\tools")
from qmp import start_vm
from serial import Console, connect

PRE = "console=ttyS0 rdinit=/init loglevel=4 vt.global_cursor_default=0 nova.debug=1"
CMD = (
    "S=$(date +%s); i=0; while [ $i -lt 20000 ]; do i=$((i+1)); done; "
    "E=$(date +%s); echo LOOP $((E-S)); printf '%s\\n' L''END"
)


def run(accel, label):
    p = start_vm(extra_args=("-smp", "1", "-m", "1024", "-append", PRE), serial="tcp", accel=accel)
    try:
        con = Console(connect())
        con.read_until("SYSTEMUI_READY", 200)
        con.read_until(r"#\s", 40)
        con.buffer = ""
        con.send(CMD)
        con.read_until("LEND", 300)
        lines = [l.strip() for l in con.transcript.splitlines() if l.strip().startswith("LOOP")]
        print(label, lines[-1] if lines else "none")
    finally:
        p.kill()


run("whpx", "whpx")
run("tcg", "tcg")
