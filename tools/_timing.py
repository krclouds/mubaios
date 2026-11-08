import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

if "DRAW_MS" not in s:
    s = s.replace("static void draw_home(NovaFB *fb, int cursor_x, int cursor_y, int hover)\n{",
                  "static void draw_home(NovaFB *fb, int cursor_x, int cursor_y, int hover)\n{\n\tstruct timespec t0, t1;\n\n\tclock_gettime(CLOCK_MONOTONIC, &t0);", 1)
    s = s.replace("""	cursor_bg_valid = 0;
	draw_cursor(fb, cursor_x, cursor_y);
}""", """	cursor_bg_valid = 0;
	draw_cursor(fb, cursor_x, cursor_y);
	clock_gettime(CLOCK_MONOTONIC, &t1);
	fprintf(stderr, "DRAW_MS %.1f\\n", (t1.tv_sec - t0.tv_sec) * 1000.0 +
		(t1.tv_nsec - t0.tv_nsec) / 1e6);
}""", 1)

# time the hover repaint path too
if "HOVER_MS" not in s:
    s = s.replace("static void repaint_icon(NovaFB *fb, int idx, int hover)\n{",
                  "static void repaint_icon(NovaFB *fb, int idx, int hover)\n{\n\tstruct timespec h0, h1;\n\n\tclock_gettime(CLOCK_MONOTONIC, &h0);", 1)
    s = s.replace("""	draw_icon(fb, x, y, &apps[idx], hover == idx);
	nova_flush_rect(fb, x - 12, top, w, bottom - top);""",
                  """	draw_icon(fb, x, y, &apps[idx], hover == idx);
	nova_flush_rect(fb, x - 12, top, w, bottom - top);
	clock_gettime(CLOCK_MONOTONIC, &h1);
	fprintf(stderr, "HOVER_MS %.1f\\n", (h1.tv_sec - h0.tv_sec) * 1000.0 +
		(h1.tv_nsec - h0.tv_nsec) / 1e6);""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("timing added", "DRAW_MS" in s, "HOVER_MS" in s)
