import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

s = s.replace('\t\t\t\tfprintf(stderr, "EVDBG t=%d %d %d k=%d\\n", ev.type, ev.x, ev.y, ev.key);\n', "")
s = s.replace('\t\t\tfprintf(stderr, "PTRDBG %d %d h=%d hover=%d\\n", ev.x, ev.y, h, hover);\n', "")

# time the flush separately: flush by hand, then draw the cursor (dirty flag now clear)
old = """	cursor_bg_valid = 0;
	draw_cursor(fb, cursor_x, cursor_y);
	clock_gettime(CLOCK_MONOTONIC, &t1);"""
new = """	cursor_bg_valid = 0;
	{
		struct timespec f0, f1;

		clock_gettime(CLOCK_MONOTONIC, &f0);
		nova_flush(fb);
		clock_gettime(CLOCK_MONOTONIC, &f1);
		fprintf(stderr, "FLUSH_MS %.1f\\n", (f1.tv_sec - f0.tv_sec) * 1000.0 +
			(f1.tv_nsec - f0.tv_nsec) / 1e6);
	}
	draw_cursor(fb, cursor_x, cursor_y);
	clock_gettime(CLOCK_MONOTONIC, &t1);"""
if old in s:
    s = s.replace(old, new, 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("flush timing:", "FLUSH_MS" in s, "evdbg removed:", "EVDBG" not in s)
