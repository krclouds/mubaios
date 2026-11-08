import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

HELPERS = r'''
/* Repaint a single icon cell from the cached wallpaper: hover changes used to
 * redraw the whole screen (wallpaper memcpy + every blend), which felt laggy. */
static int icon_rect(NovaFB *fb, int idx, int *x, int *y)
{
	int x0, y0, cols;
	int row, col;

	if (idx < 0 || idx >= app_count)
		return 0;
	grid_geometry(fb->w, &x0, &y0, &cols);
	row = idx / cols;
	col = idx % cols;
	*x = x0 + col * (ICON + GAPX);
	*y = y0 + row * (ICON + GAPY) - scroll_y;
	return *y + ICON + 40 > 150 && *y < fb->h - 140;
}

static void repaint_icon(NovaFB *fb, int idx, int hover)
{
	int x, y, w, h, top, bottom;

	if (!icon_rect(fb, idx, &x, &y))
		return;
	w = ICON + 24;
	h = ICON + 52;
	top = y - 12;
	bottom = top + h;
	if (top < 150)
		top = 150;
	if (bottom > fb->h - 130)
		bottom = fb->h - 130;
	if (bottom <= top)
		return;
	for (int row = top; row < bottom; row++) {
		int dst = row * fb->w + (x - 12);

		memcpy(fb->buf + dst, wall_buf + dst, w * 4);
	}
	draw_icon(fb, x, y, &apps[idx], hover == idx);
	nova_flush_rect(fb, x - 12, top, w, bottom - top);
}

'''
anchor = "static int max_scroll(NovaFB *fb)"
assert anchor in s
s = s.replace(anchor, HELPERS + anchor, 1)

old_move = '''			h = hit_icon(&fb, ev.x, ev.y);

			if (h != hover) {
				hover = h;
				draw_home(&fb, ev.x, ev.y, hover);
			} else {
				draw_cursor(&fb, ev.x, ev.y);
			}
			break;'''
new_move = '''			h = hit_icon(&fb, ev.x, ev.y);

			if (h != hover) {
				int old = hover;

				hover = h;
				if (old >= 0)
					repaint_icon(&fb, old, hover);
				if (h >= 0)
					repaint_icon(&fb, h, hover);
			}
			draw_cursor(&fb, ev.x, ev.y);
			break;'''
assert old_move in s
s = s.replace(old_move, new_move, 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("hover repaints only the affected icons")
