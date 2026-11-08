import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# --- helper: restore a rectangle from the cached wallpaper, redraw icons, flush just that strip
if "draw_scroll_region" not in s:
    helper = '''static void draw_scroll_region(NovaFB *fb, int hover)
{
	int x0, y0, cols;
	int top = 150, bot = fb->h - NOVA_NAVBAR_H;
	int rx, ry, rw, rh;

	grid_geometry(fb->w, &x0, &y0, &cols);
	rx = x0 - 40;
	if (rx < 0)
		rx = 0;
	rw = cols * (ICON + GAPX) + 60;
	if (rx + rw > fb->w - 16)
		rw = fb->w - 16 - rx;
	ry = top;
	rh = bot - top;

	if (wall_buf) {
		for (int y = ry; y < ry + rh; y++)
			memcpy(fb->buf + (size_t)y * fb->w + rx,
			       wall_buf + (size_t)y * fb->w + rx, (size_t)rw * 4);
	} else {
		nova_gradient(fb, 0, 0, fb->w, fb->h, 0x1d1746, 0x05050d);
	}

	for (int i = 0; i < app_count; i++) {
		int col = i % cols, row = i / cols;
		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY) - scroll_y;

		if (y < top || y > fb->h - NOVA_NAVBAR_H)
			continue;
		draw_icon(fb, x, y, &apps[i], i == hover);
	}
	{
		int ms = max_scroll(fb);

		if (ms > 0) {
			int b = fb->h - NOVA_NAVBAR_H - 18;
			int h = (b - top) * (b - top) / ((b - top) + ms);
			int ty = top + (b - top - h) * scroll_y / ms;

			nova_round_rect_blend(fb, fb->w - 22, ty, 5, h, 3, 0xdfe3f5, 90);
		}
	}
	nova_flush_rect(fb, rx, ry, rw, rh);
}

'''
    anchor = "static void draw_status_only(NovaFB *fb, const char *clk)"
    s = s.replace(anchor, helper + anchor, 1)

# --- use it for drag scrolling and wheel scrolling
s = s.replace("""					if (ns != scroll_y) {
						scroll_y = ns;
						draw_home(&fb, ev.x, ev.y, hover);
					}""",
              """					if (ns != scroll_y) {
						scroll_y = ns;
						draw_scroll_region(&fb, hover);
					}""", 1)

s = s.replace("""				if (ns != scroll_y) {
					scroll_y = ns;
					draw_home(&fb, ev.x, ev.y, hover);
				}""",
              """				if (ns != scroll_y) {
					scroll_y = ns;
					draw_scroll_region(&fb, hover);
				}""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("scroll region:", s.count("draw_scroll_region"))
