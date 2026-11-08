import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

old = """		if (strcmp(fresh, clock) != 0) {
			memcpy(clock, fresh, sizeof(clock));
			draw_home(&fb, in.x, in.y, hover);
		}"""
new = """		if (strcmp(fresh, clock) != 0) {
			memcpy(clock, fresh, sizeof(clock));
			draw_status_only(&fb, clock, date);
		}"""
if old in s:
    s = s.replace(old, new, 1)

if "draw_status_only(NovaFB" not in s:
    helper = (
        "static void draw_status_only(NovaFB *fb, const char *clk, const char *dt)\n"
        "{\n"
        "\tstruct timespec t0, t1;\n\n"
        "\tclock_gettime(CLOCK_MONOTONIC, &t0);\n"
        "\tcursor_hide(fb);\n"
        "\tandroid_status_bar(fb, clk, dt);\n"
        "\tcursor_bg_valid = 0;\n"
        "\tcursor_hide(fb);\n"
        "\tnova_flush_rect(fb, 0, 0, fb->w, 56);\n"
        "\tclock_gettime(CLOCK_MONOTONIC, &t1);\n"
        '\tfprintf(stderr, "TICK_MS %.1f\\n", (t1.tv_sec - t0.tv_sec) * 1000.0 +\n'
        "\t\t(t1.tv_nsec - t0.tv_nsec) / 1e6);\n"
        "}\n\n"
    )
    anchor = "static void draw_home(NovaFB *fb, int cursor_x, int cursor_y, int hover)"
    s = s.replace(anchor, helper + anchor, 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("tick:", "draw_status_only(&fb" in s, "helper:", "draw_status_only(NovaFB" in s)
