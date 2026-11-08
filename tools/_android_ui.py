import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")

s = open(SS, encoding="utf-8").read()

HELPERS = r'''
/* ---------------- Material-ish shell pieces ---------------- */

static int shade;                 /* 0 = closed, 1 = open */
static int tile_on[6] = {1, 0, 0, 0, 0, 1};

static struct app *find_app(const char *id)
{
	for (int i = 0; i < app_count; i++)
		if (!strcmp(apps[i].id, id))
			return &apps[i];
	return NULL;
}

static void app_glyph(NovaFB *fb, const struct app *a, int cx, int cy, int s,
		      uint32_t fg, uint32_t bg)
{
	int i, gw;

	if (!strcmp(a->id, "settings")) {
		for (i = 0; i < 8; i++) {
			int ax = cx + (int)(s * 0.50f * cosf((float)i * 0.785f));
			int ay = cy + (int)(s * 0.50f * sinf((float)i * 0.785f));

			nova_circle(fb, ax, ay, s / 11, fg);
		}
		nova_circle(fb, cx, cy, s * 37 / 100, fg);
		nova_circle(fb, cx, cy, s * 16 / 100, bg);
	} else if (!strcmp(a->id, "files")) {
		nova_round_rect(fb, cx - s * 42 / 100, cy - s * 30 / 100, s * 84 / 100,
				s * 62 / 100, s / 10, fg);
		nova_round_rect(fb, cx - s * 42 / 100, cy - s * 42 / 100, s * 38 / 100,
				s * 18 / 100, s / 16, fg);
		nova_fill(fb, cx - s * 32 / 100, cy - s * 14 / 100, s * 64 / 100,
			  s / 14, bg);
	} else if (!strcmp(a->id, "paint")) {
		for (i = -2; i <= 2; i++)
			nova_line(fb, cx - s * 34 / 100 + i, cy + s * 34 / 100 + i,
				  cx + s * 18 / 100 + i, cy - s * 18 / 100 + i, fg);
		nova_circle(fb, cx - s * 34 / 100, cy + s * 34 / 100, s / 9, fg);
		nova_circle(fb, cx + s * 24 / 100, cy - s * 24 / 100, s / 12, fg);
	} else if (!strcmp(a->id, "terminal")) {
		nova_line(fb, cx - s * 26 / 100, cy - s * 22 / 100, cx - s * 2 / 100, cy, fg);
		nova_line(fb, cx - s * 2 / 100, cy, cx - s * 26 / 100, cy + s * 22 / 100, fg);
		nova_fill(fb, cx + s * 6 / 100, cy + s * 16 / 100, s * 26 / 100, s / 10, fg);
	} else if (!strcmp(a->id, "store")) {
		nova_round_rect(fb, cx - s * 34 / 100, cy - s * 18 / 100, s * 68 / 100,
				s * 52 / 100, s / 8, fg);
		nova_circle(fb, cx, cy - s * 18 / 100, s * 20 / 100, fg);
		nova_circle(fb, cx, cy - s * 18 / 100, s * 13 / 100, bg);
	} else if (!strcmp(a->id, "clock")) {
		nova_circle(fb, cx, cy, s * 38 / 100, fg);
		nova_circle(fb, cx, cy, s * 32 / 100, bg);
		nova_line(fb, cx, cy, cx, cy - s * 22 / 100, fg);
		nova_line(fb, cx, cy, cx + s * 16 / 100, cy + s * 6 / 100, fg);
	} else if (!strcmp(a->id, "calc")) {
		nova_round_rect(fb, cx - s * 34 / 100, cy - s * 34 / 100, s * 68 / 100,
				s * 68 / 100, s / 8, fg);
		for (i = 0; i < 6; i++)
			nova_fill(fb, cx - s * 22 / 100 + (i % 3) * s * 22 / 100,
				  cy - s * 10 / 100 + (i / 3) * s * 22 / 100,
				  s / 8, s / 8, bg);
	} else if (!strcmp(a->id, "world")) {
		nova_line(fb, cx, cy - s * 34 / 100, cx + s * 32 / 100, cy - s * 16 / 100, fg);
		nova_line(fb, cx, cy - s * 34 / 100, cx - s * 32 / 100, cy - s * 16 / 100, fg);
		nova_line(fb, cx - s * 32 / 100, cy - s * 16 / 100, cx, cy + s * 4 / 100, fg);
		nova_line(fb, cx + s * 32 / 100, cy - s * 16 / 100, cx, cy + s * 4 / 100, fg);
		nova_line(fb, cx, cy + s * 4 / 100, cx, cy + s * 34 / 100, fg);
		nova_line(fb, cx - s * 32 / 100, cy - s * 16 / 100, cx - s * 32 / 100, cy + s * 14 / 100, fg);
		nova_line(fb, cx + s * 32 / 100, cy - s * 16 / 100, cx + s * 32 / 100, cy + s * 14 / 100, fg);
		nova_line(fb, cx - s * 32 / 100, cy + s * 14 / 100, cx, cy + s * 34 / 100, fg);
		nova_line(fb, cx + s * 32 / 100, cy + s * 14 / 100, cx, cy + s * 34 / 100, fg);
	} else {
		gw = nova_text_width(a->icon, 3);
		nova_text(fb, cx - gw / 2, cy - 24, a->icon, fg, 3);
	}
}

static void android_status_bar(NovaFB *fb, const char *clock, const char *date)
{
	int bx;

	nova_round_rect_blend(fb, 0, 0, fb->w, 56, 0, 0x05060c, 100);
	nova_text_shadow(fb, 26, 14, clock, NOVA_WHITE, 2);
	nova_text(fb, 26 + nova_text_width(clock, 2) + 18, 17, date, 0xa9b0c6, 2);

	bx = fb->w - 74;
	nova_round_rect(fb, bx, 18, 36, 18, 6, 0xc3c9dd);
	nova_round_rect(fb, bx + 2, 20, 26, 14, 5, NOVA_OK);
	nova_fill(fb, bx + 37, 22, 3, 10, 0xc3c9dd);
	for (int i = 0; i < 4; i++)
		nova_fill(fb, bx - 44 + i * 7, 28 - i * 4, 5, 6 + i * 4, 0xdde2f2);
}

static void draw_search(NovaFB *fb, int y)
{
	int x = 56, w = fb->w - 112, h = 58;
	uint32_t fg = 0x99a1b8;

	nova_round_rect_blend(fb, x, y, w, h, h / 2, 0x171c2c, 215);
	nova_circle(fb, x + 36, y + h / 2 - 3, 10, fg);
	nova_circle(fb, x + 36, y + h / 2 - 3, 6, 0x171c2c);
	nova_line(fb, x + 44, y + h / 2 + 5, x + 52, y + h / 2 + 13, fg);
	nova_text(fb, x + 68, y + 19, "\u641c\u7d22\u5e94\u7528", fg, 2);
}

static const char *dock_ids[4] = {"settings", "files", "terminal", "store"};

static void dock_rect(NovaFB *fb, int *x, int *y, int *w, int *h)
{
	*w = 4 * 96 + 40;
	*h = 100;
	*x = (fb->w - *w) / 2;
	*y = fb->h - *h - 34;
}

static int dock_hit(NovaFB *fb, int mx, int my)
{
	int x, y, w, h;

	dock_rect(fb, &x, &y, &w, &h);
	for (int i = 0; i < 4; i++) {
		int cx = x + 20 + i * 96 + 38;

		if (nova_hit(mx, my, cx - 44, y, 88, h))
			return i;
	}
	return -1;
}

static void draw_dock(NovaFB *fb)
{
	int x, y, w, h;

	dock_rect(fb, &x, &y, &w, &h);
	nova_shadow(fb, x, y + 6, w, h, h / 2, 5, 120);
	nova_round_rect_blend(fb, x, y, w, h, h / 2, 0x0f1322, 205);
	nova_round_rect_blend(fb, x + 2, y + 2, w - 4, h / 2, h / 2, 0xffffff, 10);

	for (int i = 0; i < 4; i++) {
		struct app *a = find_app(dock_ids[i]);
		int cx = x + 20 + i * 96 + 38;
		int s = 68;
		uint32_t top = nova_mix(a ? a->color : 0x333a55, 0xffffff, 36);
		uint32_t bot = nova_mix(a ? a->color : 0x333a55, 0x05060c, 86);

		if (!a)
			continue;
		nova_squircle(fb, cx - s / 2, y + (h - s) / 2 - 4, s, s, top, bot);
		app_glyph(fb, a, cx, y + (h - s) / 2 - 4 + s / 2, s, NOVA_WHITE, bot);
	}
	nova_round_rect(fb, fb->w / 2 - 62, fb->h - 15, 124, 5, 3, 0x353d5e);
}

static void shade_tile_rect(NovaFB *fb, int i, int *x, int *y, int *w, int *h)
{
	int cols = 3, gap = 16, x0 = 56;
	int tw = (fb->w - 2 * x0 - (cols - 1) * gap) / cols;

	*w = tw;
	*h = 96;
	*x = x0 + (i % cols) * (tw + gap);
	*y = 158 + (i / cols) * (96 + gap);
}

static void draw_shade(NovaFB *fb)
{
	static const char *labels[6] = {
		"\u65e0\u7ebf\u7f51\u7edc", "\u84dd\u7259", "\u52ff\u6270\u6a21\u5f0f",
		"\u98de\u884c\u6a21\u5f0f", "\u624b\u7535\u7b52", "\u81ea\u52a8\u65cb\u8f6c"
	};

	nova_round_rect_blend(fb, 0, 0, fb->w, fb->h, 0, 0x05060c, 130);
	nova_round_rect_gradient(fb, 0, 0, fb->w, 476, 36, 0x1c2238, 0x111527);
	nova_text(fb, 56, 72, "NovaOS", NOVA_WHITE, 3);
	nova_text(fb, 56, 118, "\u5feb\u6377\u8bbe\u7f6e", 0x8f96ad, 2);

	for (int i = 0; i < 6; i++) {
		int x, y, w, h;

		shade_tile_rect(fb, i, &x, &y, &w, &h);
		nova_round_rect(fb, x, y, w, h, 26, tile_on[i] ? 0x2f3a63 : 0x1a2032);
		nova_circle(fb, x + 34, y + 34, 16, tile_on[i] ? 0xa9b6ff : 0x3a4160);
		nova_text(fb, x + 24, y + 62, labels[i], tile_on[i] ? NOVA_WHITE : 0x9aa0b5, 2);
	}

	/* brightness slider */
	nova_text(fb, 56, 372, "\u4eae\u5ea6", 0x9aa0b5, 2);
	nova_round_rect(fb, 56, 404, fb->w - 112, 26, 13, 0x1a2032);
	nova_round_rect(fb, 56, 404, (fb->w - 112) * 68 / 100, 26, 13, 0x6c5ce7);

	nova_round_rect(fb, 56, 456, fb->w - 112, 78, 24, 0x232a3e);
	nova_circle(fb, 92, 484, 14, 0x3a4160);
	nova_text(fb, 118, 466, "\u6ca1\u6709\u901a\u77e5", NOVA_WHITE, 2);
	nova_text(fb, 118, 498, "NovaOS 0.1", 0x8f96ad, 2);
}

'''
anchor = "static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)"
assert anchor in s
s = s.replace(anchor, HELPERS + anchor, 1)

# icons now use pictograms
old_glyph = '''	gw = nova_text_width(a->icon, 3);
	nova_text(fb, x + (ICON - gw) / 2, y + (ICON - 48) / 2, a->icon, NOVA_WHITE, 3);

	nw = nova_text_width(a->name, 2);'''
new_glyph = '''	app_glyph(fb, a, x + ICON / 2, y + ICON / 2, ICON, NOVA_WHITE, bottom);

	nw = nova_text_width(a->name, 2);'''
assert old_glyph in s
s = s.replace(old_glyph, new_glyph, 1)
s = s.replace("	uint32_t bottom = nova_mix(a->color, 0x05060c, 84);\n	int gw, nw;",
              "	uint32_t bottom = nova_mix(a->color, 0x05060c, 84);\n	int nw;", 1)

# grid moves down to leave room for the search pill
s = s.replace("	*y0 = 190;", "	*y0 = 268;", 1)

# home: android status bar + search pill + dock + shade
old_sb = '''	nova_status_bar(fb, "NovaOS", clock);'''
new_sb = '''	android_status_bar(fb, clock, date);
	draw_search(fb, 170);'''
assert old_sb in s
s = s.replace(old_sb, new_sb, 1)

old_nav = '''	draw_nav(fb, 0, 0, 0);'''
new_nav = '''	draw_dock(fb);
	if (shade)
		draw_shade(fb);'''
assert old_nav in s
s = s.replace(old_nav, new_nav, 1)

# tap handling: dock + shade
old_up = '''			idx = hit_icon(&fb, ev.x, ev.y);
			nav = hit_nav(&fb, ev.x, ev.y);'''
new_up = '''			if (shade) {
				int hit = -1;

				for (int i = 0; i < 6; i++) {
					int tx, ty, tw, th;

					shade_tile_rect(&fb, i, &tx, &ty, &tw, &th);
					if (nova_hit(ev.x, ev.y, tx, ty, tw, th))
						hit = i;
				}
				if (hit >= 0) {
					tile_on[hit] = !tile_on[hit];
				} else if (ev.y > 480) {
					shade = 0;
				}
				draw_home(&fb, ev.x, ev.y, hover);
				pressed = -1;
				nav_pressed = -1;
				break;
			}
			if (ev.y < 56) {
				shade = 1;
				draw_home(&fb, ev.x, ev.y, hover);
				pressed = -1;
				nav_pressed = -1;
				break;
			}
			idx = hit_icon(&fb, ev.x, ev.y);
			nav = hit_nav(&fb, ev.x, ev.y);
			if (idx < 0) {
				int di = dock_hit(&fb, ev.x, ev.y);

				if (di >= 0) {
					struct app *da = find_app(dock_ids[di]);

					if (da && pressed == -2) {
						ripple_at(&fb, ev.x, ev.y);
						launch_app(da);
					}
					draw_home(&fb, ev.x, ev.y, hover);
					pressed = -1;
					nav_pressed = -1;
					break;
				}
			}'''
assert old_up in s
s = s.replace(old_up, new_up, 1)

# ESC closes the shade
old_esc = '''		case NOVA_KEY:
			if (ev.key == 1) /* ESC returns to home */
				draw_home(&fb, ev.x, ev.y, hover);'''
new_esc = '''		case NOVA_KEY:
			if (ev.key == 1) { /* ESC returns to home */
				shade = 0;
				draw_home(&fb, ev.x, ev.y, hover);
			}'''
assert old_esc in s
s = s.replace(old_esc, new_esc, 1)

# mark dock presses as -2 so the release knows where it came from
old_down = '''			pressed = hit_icon(&fb, ev.x, ev.y);
			nav_pressed = hit_nav(&fb, ev.x, ev.y);'''
new_down = '''			pressed = hit_icon(&fb, ev.x, ev.y);
			if (pressed < 0 && dock_hit(&fb, ev.x, ev.y) >= 0)
				pressed = -2;
			nav_pressed = hit_nav(&fb, ev.x, ev.y);'''
assert old_down in s
s = s.replace(old_down, new_down, 1)

# ripple helper right before launch_app
ripple = '''static void ripple_at(NovaFB *fb, int cx, int cy)
{
	for (int step = 0; step < 3; step++) {
		int r = 18 + step * 20;

		for (int y = cy - r; y <= cy + r; y++)
			for (int x = cx - r; x <= cx + r; x++) {
				int dx = x - cx, dy = y - cy, d2 = dx * dx + dy * dy;

				if (d2 <= r * r && d2 > (r - 9) * (r - 9))
					nova_blend_px(fb, x, y, 0xffffff, 70 - step * 22);
			}
		nova_flush(fb);
		usleep(26000);
	}
}

'''
anchor2 = "static void launch_app(const struct app *a)"
assert anchor2 in s
s = s.replace(anchor2, ripple + anchor2, 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("android shell patched")
