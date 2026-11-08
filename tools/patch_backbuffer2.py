import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs):
    p = os.path.join(SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s:
            print("MISS", name, a[:50].replace("\n", "\\n"))
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


patch("nova.c", [
    # dirty tracking
    ("static uint32_t cursor_bg[24 * 24];",
     "static int fb_dirty;\nstatic uint32_t cursor_bg[24 * 24];"),
    ("void nova_flush(NovaFB *fb)\n{",
     "void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h)\n"
     "{\n"
     "	int x0 = x < 0 ? 0 : x, y0 = y < 0 ? 0 : y;\n"
     "	int x1 = x + w > fb->w ? fb->w : x + w;\n"
     "	int y1 = y + h > fb->h ? fb->h : y + h;\n"
     "\n"
     "	if (!fb->buf || fb->bpp != 32 || x1 <= x0 || y1 <= y0)\n"
     "\t\treturn;\n"
     "	for (int yy = y0; yy < y1; yy++)\n"
     "\t\tmemcpy(fb->mem + (size_t)yy * fb->stride + (size_t)x0 * 4,\n"
     "\t\t       fb->buf + (size_t)yy * fb->w + x0, (size_t)(x1 - x0) * 4);\n"
     "}\n"
     "\nvoid nova_flush(NovaFB *fb)\n{"),
    ("		       fb->buf + (size_t)y * fb->w, (size_t)fb->w * 4);\n}",
     "		       fb->buf + (size_t)y * fb->w, (size_t)fb->w * 4);\n\tfb_dirty = 0;\n}"),
    # mark dirty from the primitives
    ("	if (fb->bpp == 32) {\n\t\tfb->buf[(size_t)y * fb->w + x] = c;",
     "	if (fb->bpp == 32) {\n\t\tfb->buf[(size_t)y * fb->w + x] = c;\n\t\tfb_dirty = 1;"),
    ("		for (int xx = x0; xx < x1; xx++)\n\t\t\trow[xx] = color;",
     "		fb_dirty = 1;\n\t\tfor (int xx = x0; xx < x1; xx++)\n\t\t\trow[xx] = color;"),
    # cursor: flush only what moved when nothing else was drawn
    ("""	cursor_bg_x = x - 9;
	cursor_bg_y = y - 9;
	cursor_bg_valid = 1;
	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
}""",
     """	cursor_bg_x = x - 9;
	cursor_bg_y = y - 9;
	cursor_bg_valid = 1;
	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
	if (fb_dirty) {
		nova_flush(fb);
	} else {
		if (had_bg)
			nova_flush_rect(fb, old_x, old_y, 24, 24);
		nova_flush_rect(fb, x - 9, y - 9, 24, 24);
	}
}"""),
    ("""void nova_cursor_draw(NovaFB *fb, int x, int y)
{
	if (cursor_bg_valid) {""",
     """void nova_cursor_draw(NovaFB *fb, int x, int y)
{
	int had_bg = cursor_bg_valid, old_x = cursor_bg_x, old_y = cursor_bg_y;

	if (cursor_bg_valid) {"""),
])

# world: upscale into the back buffer
patch("world.c", [
    ("""		uint8_t *d0 = fb->mem + (size_t)(2 * y) * fb->stride;
		uint8_t *d1 = fb->mem + (size_t)(2 * y + 1) * fb->stride;""",
     """		uint32_t *d0 = fb->buf + (size_t)(2 * y) * fb->w;
		uint32_t *d1 = fb->buf + (size_t)(2 * y + 1) * fb->w;"""),
])

# header for the new helper
patch("nova.h", [
    ("void nova_flush(NovaFB *fb);",
     "void nova_flush(NovaFB *fb);\nvoid nova_flush_rect(NovaFB *fb, int x, int y, int w, int h);"),
])
print("dirty tracking + world adaption done")
