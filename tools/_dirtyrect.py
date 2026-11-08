import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVA_C = os.path.join(ROOT, "src", "nova.c")
s = open(NOVA_C, encoding="utf-8").read()

# dirty-rectangle tracking: remembers the bounding box of everything drawn since the last flush
if "dirty_x0" not in s:
    s = s.replace("static int fb_dirty;",
                  "static int fb_dirty;\n"
                  "static int dirty_x0, dirty_y0, dirty_x1, dirty_y1;\n"
                  "static int dirty_valid;\n\n"
                  "static inline void dirty_add(int x, int y)\n"
                  "{\n"
                  "\tif (!dirty_valid) {\n"
                  "\t\tdirty_x0 = dirty_x1 = x;\n"
                  "\t\tdirty_y0 = dirty_y1 = y;\n"
                  "\t\tdirty_valid = 1;\n"
                  "\t\treturn;\n"
                  "\t}\n"
                  "\tif (x < dirty_x0) dirty_x0 = x;\n"
                  "\tif (x > dirty_x1) dirty_x1 = x;\n"
                  "\tif (y < dirty_y0) dirty_y0 = y;\n"
                  "\tif (y > dirty_y1) dirty_y1 = y;\n"
                  "}\n\n"
                  "static inline void dirty_clear(void)\n"
                  "{\n"
                  "\tdirty_valid = 0;\n"
                  "}\n", 1)

    s = s.replace("""	if (fb->bpp == 32) {
		fb->buf[(size_t)y * fb->w + x] = c;
		fb_dirty = 1;""",
                  """	if (fb->bpp == 32) {
		fb->buf[(size_t)y * fb->w + x] = c;
		fb_dirty = 1;
		dirty_add(x, y);""", 1)

    # flush() and flush_rect() reset the tracked box
    s = s.replace("""	fb_dirty = 0;
}

static int isqrt_i""",
                  """	fb_dirty = 0;
	dirty_clear();
}

static int isqrt_i""", 1)

    s = s.replace("""	for (int yy = y0; yy < y1; yy++)
		memcpy(fb->mem + (size_t)yy * fb->stride + (size_t)x0 * 4,
		       fb->buf + (size_t)yy * fb->w + x0, (size_t)(x1 - x0) * 4);""",
                  """	for (int yy = y0; yy < y1; yy++)
		memcpy(fb->mem + (size_t)yy * fb->stride + (size_t)x0 * 4,
		       fb->buf + (size_t)yy * fb->w + x0, (size_t)(x1 - x0) * 4);
	if (x0 <= dirty_x0 && y0 <= dirty_y0 && x1 > dirty_x1 && y1 > dirty_y1)
		dirty_clear();""", 1)

    # cursor draw: flush just the dirty box instead of the whole screen
    s = s.replace("""	if (was_dirty) {
		nova_flush(fb);""",
                  """	if (was_dirty && dirty_valid) {
		int bx0 = dirty_x0 - 10 < 0 ? 0 : dirty_x0 - 10;
		int by0 = dirty_y0 - 10 < 0 ? 0 : dirty_y0 - 10;
		int bx1 = dirty_x1 + 10 >= fb->w ? fb->w : dirty_x1 + 11;
		int by1 = dirty_y1 + 10 >= fb->h ? fb->h : dirty_y1 + 11;

		nova_flush_rect(fb, bx0, by0, bx1 - bx0, by1 - by0);
		fb_dirty = 0;
		dirty_clear();
	} else if (was_dirty) {
		nova_flush(fb);""", 1)

open(NOVA_C, "w", encoding="utf-8", newline="\n").write(s)
print("dirty rect:", "dirty_add" in s, "| cursor rect flush:", "nova_flush_rect(fb, bx0, by0" in s)
