import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

if "PTRDBG" not in s:
    s = s.replace("""			h = hit_icon(&fb, ev.x, ev.y);

			if (h != hover) {""",
                  """			h = hit_icon(&fb, ev.x, ev.y);
			fprintf(stderr, "PTRDBG %d %d h=%d hover=%d\\n", ev.x, ev.y, h, hover);

			if (h != hover) {""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("ptr debug:", "PTRDBG" in s)
