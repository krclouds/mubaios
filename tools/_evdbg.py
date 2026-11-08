import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

if "EVDBG" not in s:
    # log every input event right after it is polled
    idx = s.find("if (nova_poll(&in, &ev, 250) == 0) {")
    if idx < 0:
        idx = s.find("if (nova_poll(&in, &ev")
    seg = s[idx:idx + 400]
    nl = s.find("\n", s.find("{", idx))
    s = s[:nl + 1] + '\t\t\tfprintf(stderr, "EVDBG t=%d %d %d k=%d\\n", ev.type, ev.x, ev.y, ev.key);\n' + s[nl + 1:]

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("event debug:", "EVDBG" in s)
print(s[s.find("EVDBG") - 200:s.find("EVDBG") + 120])
