import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "src", "system_server.c")

s = io.open(P, encoding="utf-8").read()

# 1. scroll state + helper -------------------------------------------------
s = s.replace(
    "static struct app apps[64];\nstatic int app_count;",
    "static struct app apps[64];\nstatic int app_count;\nstatic int scroll_y;")

helper = '''
static int max_scroll(NovaFB *fb)
{
	int x0, y0, cols, rows, content, view;

	grid_geometry(fb->w, &x0, &y0, &cols);
	rows = (app_count + cols - 1) / cols;
	content = y0 + rows * (ICON + GAPY) - GAPY + ICON + 44;
	view = fb->h - NOVA_NAVBAR_H - 40;
	if (content <= view)
		return 0;
	return content - view;
}

static int clamp_scroll(NovaFB *fb, int v)
{
	int ms = max_scroll(fb);

	if (v < 0)
		v = 0;
	if (v > ms)
		v = ms;
	return v;
}
'''
s = s.replace("static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)",
              helper + "\nstatic void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)")

# 2. draw icons with the scroll offset + a scrollbar -----------------------
s = s.replace(
    '''	for (int i = 0; i < app_count; i++) {
		int col = i % cols;
		int row = i / cols;
		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY);
		draw_icon(fb, x, y, &apps[i], i == hover);
	}''',
    '''	for (int i = 0; i < app_count; i++) {
		int col = i % cols;
		int row = i / cols;
		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY) - scroll_y;

		if (y + ICON + 44 < 60 || y > fb->h - NOVA_NAVBAR_H)
			continue;
		draw_icon(fb, x, y, &apps[i], i == hover);
	}
	{
		int ms = max_scroll(fb);

		if (ms > 0) {
			int top = 150, bot = fb->h - NOVA_NAVBAR_H - 18;
			int h = (bot - top) * (bot - top) / ((bot - top) + ms);
			int ty = top + (bot - top - h) * scroll_y / ms;

			nova_round_rect(fb, fb->w - 24, ty, 8, h, 4, 0x5a5f7a);
		}
	}''')

# 3. hit test respects the offset -----------------------------------------
s = s.replace(
    '''		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY);
		if (nova_hit(mx, my, x - 6, y - 6, ICON + 12, ICON + 12))
			return i;''',
    '''		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY) - scroll_y;

		if (y + ICON < 60 || y > fb->h - NOVA_NAVBAR_H)
			continue;
		if (nova_hit(mx, my, x - 6, y - 6, ICON + 12, ICON + 12))
			return i;''')

# 4. drag to scroll --------------------------------------------------------
s = s.replace(
    "	int hover = -1, pressed = -1, nav_pressed = -1;",
    "	int hover = -1, pressed = -1, nav_pressed = -1;\n	int pressing = 0, dragged = 0, drag_y = 0, drag_scroll = 0;")

s = s.replace(
    '''		case NOVA_MOVE: {
			int h = hit_icon(&fb, ev.x, ev.y);''',
    '''		case NOVA_MOVE: {
			int h;

			if (pressing) {
				int dy = ev.y - drag_y;

				if (!dragged && (dy > 10 || dy < -10))
					dragged = 1;
				if (dragged) {
					int ns = clamp_scroll(&fb, drag_scroll - dy);

					if (ns != scroll_y) {
						scroll_y = ns;
						draw_home(&fb, ev.x, ev.y, hover);
					}
					draw_cursor(&fb, ev.x, ev.y);
					break;
				}
			}
			h = hit_icon(&fb, ev.x, ev.y);''')

s = s.replace(
    '''		case NOVA_DOWN:
			pressed = hit_icon(&fb, ev.x, ev.y);
			nav_pressed = hit_nav(&fb, ev.x, ev.y);
			break;''',
    '''		case NOVA_DOWN:
			pressing = 1;
			dragged = 0;
			drag_y = ev.y;
			drag_scroll = scroll_y;
			pressed = hit_icon(&fb, ev.x, ev.y);
			nav_pressed = hit_nav(&fb, ev.x, ev.y);
			break;
		case NOVA_WHEEL:
			scroll_y = clamp_scroll(&fb, scroll_y - ev.value * 70);
			draw_home(&fb, ev.x, ev.y, hover);
			break;''')

s = s.replace(
    '''		case NOVA_UP: {
			int idx = hit_icon(&fb, ev.x, ev.y);
			int nav = hit_nav(&fb, ev.x, ev.y);

			if (nav == 3) {''',
    '''		case NOVA_UP: {
			int idx, nav;

			pressing = 0;
			if (dragged) {
				dragged = 0;
				pressed = -1;
				nav_pressed = -1;
				break;
			}
			idx = hit_icon(&fb, ev.x, ev.y);
			nav = hit_nav(&fb, ev.x, ev.y);
			if (nav == 3) {''')

io.open(P, "w", encoding="utf-8").write(s)
print("launcher scrolling added")
