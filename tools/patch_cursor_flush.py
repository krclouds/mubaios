import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs):
    p = os.path.join(SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s:
            print("MISS", name, a[:60].replace("\n", "\\n"))
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


patch("nova.h", [
    ("void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h);",
     "void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h);\nint nova_dirty(void);"),
])

patch("nova.c", [
    ("void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h)\n{",
     "int nova_dirty(void)\n{\n\treturn fb_dirty;\n}\n\nvoid nova_flush_rect(NovaFB *fb, int x, int y, int w, int h)\n{"),
    ("""	int had_bg = cursor_bg_valid, old_x = cursor_bg_x, old_y = cursor_bg_y;""",
     """	int had_bg = cursor_bg_valid, old_x = cursor_bg_x, old_y = cursor_bg_y;
	int was_dirty = fb_dirty;"""),
    ("""	if (fb_dirty) {
		nova_flush(fb);
	} else {""",
     """	if (was_dirty) {
		nova_flush(fb);
	} else {"""),
])

patch("system_server.c", [
    ("""static void draw_cursor(NovaFB *fb, int x, int y)
{""",
     """static void draw_cursor(NovaFB *fb, int x, int y)
{
	int was_dirty = nova_dirty();
	int old_x = cursor_bg_x, old_y = cursor_bg_y, had_bg = cursor_bg_valid;"""),
    ("""	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
	nova_flush(fb);
}""",
     """	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
	if (was_dirty) {
		nova_flush(fb);
	} else {
		if (had_bg)
			nova_flush_rect(fb, old_x, old_y, 24, 24);
		nova_flush_rect(fb, x - 9, y - 9, 24, 24);
	}
}"""),
])
print("cursor flushing optimised")
