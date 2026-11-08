import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nova_c = os.path.join(ROOT, "src", "nova.c")
ss_c = os.path.join(ROOT, "src", "system_server.c")

HELPERS = r'''
/* ---------------- soft & translucent primitives ---------------- */

uint32_t nova_mix(uint32_t a, uint32_t b, int t)
{
	int ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
	int br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;

	if (t <= 0)
		return a;
	if (t >= 255)
		return b;
	ar += (br - ar) * t / 255;
	ag += (bg - ag) * t / 255;
	ab += (bb - ab) * t / 255;
	return (uint32_t)((ar << 16) | (ag << 8) | ab);
}

void nova_blend_px(NovaFB *fb, int x, int y, uint32_t c, int alpha)
{
	if (alpha <= 0 || x < 0 || y < 0 || x >= fb->w || y >= fb->h)
		return;
	if (alpha >= 255) {
		put_px(fb, x, y, c);
		return;
	}
	put_px(fb, x, y, nova_mix(nova_get(fb, x, y), c, alpha));
}

static int rect_inset(int r, int dy)
{
	if (r <= 0 || dy >= r)
		return 0;
	return r - isqrt_i(r * r - (r - dy) * (r - dy));
}

void nova_round_rect_blend(NovaFB *fb, int x, int y, int w, int h, int r,
			   uint32_t c, int alpha)
{
	if (r * 2 > w)
		r = w / 2;
	if (r * 2 > h)
		r = h / 2;
	for (int dy = 0; dy < h; dy++) {
		int inset = dy < r ? rect_inset(r, dy)
			  : (dy >= h - r ? rect_inset(r, h - 1 - dy) : 0);

		for (int dx = inset; dx < w - inset; dx++)
			nova_blend_px(fb, x + dx, y + dy, c, alpha);
	}
}

void nova_shadow(NovaFB *fb, int x, int y, int w, int h, int r, int blur, int alpha)
{
	for (int i = blur; i > 0; i--) {
		int a = alpha * (blur - i + 1) / (blur + 1);

		if (a > 0)
			nova_round_rect_blend(fb, x - i, y - i, w + 2 * i, h + 2 * i,
					      r + i, 0x000000, a);
	}
}

void nova_glow(NovaFB *fb, int cx, int cy, int r, uint32_t c, int alpha)
{
	int r2 = r * r;

	for (int y = cy - r; y <= cy + r; y++) {
		if (y < 0 || y >= fb->h)
			continue;
		for (int x = cx - r; x <= cx + r; x++) {
			int dx, dy, d, a, d2;

			if (x < 0 || x >= fb->w)
				continue;
			dx = x - cx;
			dy = y - cy;
			d2 = dx * dx + dy * dy;
			if (d2 > r2)
				continue;
			d = isqrt_i(d2);
			a = alpha * (r - d) / r;
			a = a * a / 255;
			if (a > 0)
				nova_blend_px(fb, x, y, c, a);
		}
	}
}

void nova_squircle(NovaFB *fb, int x, int y, int w, int h,
		   uint32_t top, uint32_t bottom)
{
	int r = w * 30 / 100;

	nova_round_rect_gradient(fb, x, y, w, h, r, top, bottom);
	nova_round_rect_blend(fb, x + w / 12, y + h / 24, w - w / 6, h / 3,
			      r - r / 3, 0xffffff, 16);
}

void nova_text_shadow(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale)
{
	nova_text(fb, x + scale, y + scale, s, 0x07080f, scale);
	nova_text(fb, x, y, s, color, scale);
}
'''

STATUS_OLD = '''void nova_status_bar(NovaFB *fb, const char *left, const char *right)
{
	nova_fill(fb, 0, 0, fb->w, NOVA_STATUSBAR_H, 0x11131c);
	nova_text(fb, 24, 14, left, NOVA_WHITE, 2);
	int rw = nova_text_width(right, 2);
	nova_text(fb, fb->w - rw - 24, 14, right, NOVA_TEXT, 2);
	/* battery */
	int bx = fb->w - rw - 24 - 60;
	nova_round_rect(fb, bx, 15, 40, 18, 4, NOVA_DIM);
	nova_fill(fb, bx + 3, 18, 28, 12, NOVA_OK);
	nova_fill(fb, bx + 40, 20, 4, 8, NOVA_DIM);
	/* signal bars */
	for (int i = 0; i < 4; i++)
		nova_fill(fb, bx - 40 + i * 7, 30 - i * 4, 5, 4 + i * 4, NOVA_TEXT);
}'''

STATUS_NEW = '''void nova_status_bar(NovaFB *fb, const char *left, const char *right)
{
	int rw, bx;

	nova_round_rect_blend(fb, 0, 0, fb->w, NOVA_STATUSBAR_H, 0, 0x080a12, 140);
	nova_text_shadow(fb, 24, 12, left, NOVA_WHITE, 2);
	rw = nova_text_width(right, 2);
	nova_text_shadow(fb, fb->w - rw - 24, 12, right, NOVA_WHITE, 2);
	/* battery */
	bx = fb->w - rw - 24 - 52;
	nova_round_rect(fb, bx, 15, 34, 16, 4, 0x9aa0b8);
	nova_round_rect(fb, bx + 2, 17, 24, 12, 3, NOVA_OK);
	nova_fill(fb, bx + 35, 19, 3, 8, 0x9aa0b8);
	/* signal bars */
	for (int i = 0; i < 4; i++)
		nova_fill(fb, bx - 34 + i * 6, 26 - i * 4, 4, 4 + i * 4, 0xd6dbec);
}'''

BACK_OLD = '''void nova_back_button(NovaFB *fb, int cx, int cy, int r)
{
	nova_circle(fb, cx, cy, r, 0x2a2f40);
	nova_line(fb, cx + r / 3, cy - r / 2, cx - r / 2, cy, NOVA_WHITE);
	nova_line(fb, cx - r / 2, cy, cx + r / 3, cy + r / 2, NOVA_WHITE);
	nova_line(fb, cx + r / 3, cy - r / 2, cx + r / 3, cy + r / 2, NOVA_WHITE);
}'''

BACK_NEW = '''void nova_back_button(NovaFB *fb, int cx, int cy, int r)
{
	nova_shadow(fb, cx - r, cy - r + 2, 2 * r, 2 * r, r, 8, 110);
	nova_circle(fb, cx, cy, r, 0x3b4266);
	nova_circle(fb, cx, cy - 2, r - 3, 0x2b3150);
	nova_line(fb, cx + r / 3, cy - r / 2, cx - r / 2, cy, NOVA_WHITE);
	nova_line(fb, cx - r / 2, cy, cx + r / 3, cy + r / 2, NOVA_WHITE);
	nova_line(fb, cx + r / 3, cy - r / 2, cx + r / 3, cy + r / 2, NOVA_WHITE);
}'''

HEADER_OLD = '''	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x141726, 0x0b0d15);
	nova_clock(clock, sizeof(clock));
	nova_status_bar(fb, "NovaOS", clock);
	nova_back_button(fb, 56, 96, 26);
	nova_text(fb, 104, 82, title, NOVA_WHITE, 3);
	nova_fill(fb, 0, 130, fb->w, 2, 0x232838);'''

HEADER_NEW = '''	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x161b30, 0x0a0c14);
	nova_glow(fb, fb->w - 40, -30, 260, 0x6c5ce7, 46);
	nova_glow(fb, -40, fb->h + 30, 240, 0x2f7bff, 26);
	nova_clock(clock, sizeof(clock));
	nova_status_bar(fb, "NovaOS", clock);
	nova_back_button(fb, 56, 96, 26);
	nova_text_shadow(fb, 104, 82, title, NOVA_WHITE, 3);
	nova_round_rect_blend(fb, 0, 130, fb->w, 2, 0, 0x2a3050, 120);'''

ICON_OLD = '''static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)
{
	uint32_t top = a->color;
	uint32_t bottom = (a->color & 0xfefefe) >> 1;

	if (hover)
		nova_round_rect(fb, x - 6, y - 6, ICON + 12, ICON + 12, 38, 0x3a3f55);
	nova_round_rect(fb, x + 4, y + 6, ICON, ICON, 30, 0x0d0f18);
	nova_round_rect_gradient(fb, x, y, ICON, ICON, 30, top, bottom);

	int gw = nova_text_width(a->icon, 3);
	nova_text(fb, x + (ICON - gw) / 2, y + (ICON - 48) / 2, a->icon, NOVA_WHITE, 3);

	int nw = nova_text_width(a->name, 2);
	nova_text(fb, x + (ICON - nw) / 2, y + ICON + 14, a->name, NOVA_TEXT, 2);
}'''

ICON_NEW = '''static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)
{
	uint32_t top = nova_mix(a->color, 0xffffff, 40);
	uint32_t bottom = nova_mix(a->color, 0x05060c, 84);
	int gw, nw;

	if (hover)
		nova_round_rect(fb, x - 9, y - 9, ICON + 18, ICON + 18, 44, 0x272d47);
	nova_shadow(fb, x, y + 4, ICON, ICON, 34, 12, 130);
	nova_squircle(fb, x, y, ICON, ICON, top, bottom);

	gw = nova_text_width(a->icon, 3);
	nova_text_shadow(fb, x + (ICON - gw) / 2, y + (ICON - 48) / 2, a->icon, NOVA_WHITE, 3);

	nw = nova_text_width(a->name, 2);
	nova_text_shadow(fb, x + (ICON - nw) / 2, y + ICON + 12, a->name, 0xe8eaf6, 2);
}'''

NAV_OLD = '''	int cx = fb->w / 2;
	(void)hover_back;
	(void)hover_home;
	(void)hover_recent;

	/* back: triangle */
	nova_line(fb, cx - 170, y + 24, cx - 146, y + 36, NOVA_DIM);
	nova_line(fb, cx - 146, y + 36, cx - 170, y + 48, NOVA_DIM);
	nova_line(fb, cx - 170, y + 24, cx - 170, y + 48, NOVA_DIM);

	/* home: circle */
	nova_circle(fb, cx, y + 36, 13, 0x2a2f40);
	nova_circle(fb, cx, y + 36, 8, 0x0b0d14);

	/* recents: two rounded squares */
	nova_round_rect(fb, cx + 150, y + 25, 20, 22, 4, 0x2a2f40);
	nova_round_rect(fb, cx + 158, y + 31, 20, 22, 4, 0x0b0d14);'''

NAV_NEW = '''	int cx = fb->w / 2;
	int pw = 360, ph = 52, px = cx - pw / 2, py = y + 10;

	(void)hover_back;
	(void)hover_home;
	(void)hover_recent;

	nova_shadow(fb, px, py + 4, pw, ph, ph / 2, 12, 130);
	nova_round_rect_blend(fb, px, py, pw, ph, ph / 2, 0x0e1120, 175);
	nova_round_rect_blend(fb, px + 1, py + 1, pw - 2, ph / 2, ph / 2, 0xffffff, 12);

	/* back chevron */
	nova_line(fb, px + 64, py + 18, px + 46, py + 26, 0xcfd4e6);
	nova_line(fb, px + 46, py + 26, px + 64, py + 34, 0xcfd4e6);
	nova_line(fb, px + 64, py + 18, px + 64, py + 34, 0xcfd4e6);

	/* home ring */
	nova_circle(fb, cx, py + 26, 13, 0x3a4166);
	nova_circle(fb, cx, py + 26, 7, 0x0e1120);

	/* recents */
	nova_round_rect(fb, px + pw - 78, py + 16, 18, 20, 4, 0x3a4166);
	nova_round_rect(fb, px + pw - 70, py + 22, 18, 20, 4, 0x0e1120);

	/* gesture bar */
	nova_round_rect(fb, cx - 60, fb->h - 13, 120, 5, 3, 0x2c3350);'''

WALLPAPER_FUNCS = '''static uint32_t *wall_buf;
static size_t wall_len;

static void build_wallpaper(NovaFB *fb)
{
	size_t n = (size_t)fb->w * fb->h;

	wall_buf = malloc(n * 4);
	wall_len = wall_buf ? n : 0;
	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x191234, 0x06060f);
	nova_glow(fb, fb->w - 90, 80, 420, 0x7a5cff, 88);
	nova_glow(fb, 60, fb->h - 100, 360, 0x2f7bff, 66);
	nova_glow(fb, fb->w / 2 + 140, fb->h / 2, 420, 0xb44cff, 30);
	for (int yy = fb->h - 260; yy < fb->h; yy++) {
		int a = 140 * (yy - (fb->h - 260)) / 260;

		for (int xx = 0; xx < fb->w; xx++)
			nova_blend_px(fb, xx, yy, 0x05060c, a);
	}
	if (wall_buf)
		memcpy(wall_buf, fb->buf, n * 4);
}

'''

HOME_OLD = '''	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x241a4a, 0x0d0a18);

	/* a couple of soft circles for depth */
	nova_circle(fb, fb->w - 120, 140, 220, 0x2c2060);
	nova_circle(fb, 80, fb->h - 220, 180, 0x1d1547);

	nova_status_bar(fb, "NovaOS", clock);'''

HOME_NEW = '''	if (!wall_buf)
		build_wallpaper(fb);
	else
		memcpy(fb->buf, wall_buf, wall_len * 4);

	nova_status_bar(fb, "NovaOS", clock);'''

NOVA_ANCHOR = '''void nova_key_ascii'''
SS_ANCHOR = '''static void draw_home(NovaFB *fb, int cursor_x, int cursor_y, int hover)'''


def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            print("MISS in", os.path.basename(path), ":", old.splitlines()[0][:60])
            continue
        s = s.replace(old, new, 1)
    open(path, "w", encoding="utf-8", newline="\n").write(s)


# 1. nova.c: append helpers at the end of the file
with open(nova_c, "a", encoding="utf-8", newline="\n") as f:
    f.write(HELPERS)

# 2. nova.c widget restyle
patch(nova_c, [(STATUS_OLD, STATUS_NEW), (BACK_OLD, BACK_NEW), (HEADER_OLD, HEADER_NEW)])

# 3. system_server: wallpaper cache + new icon/nav
patch(ss_c, [(SS_ANCHOR, WALLPAPER_FUNCS + SS_ANCHOR),
             (ICON_OLD, ICON_NEW),
             (NAV_OLD, NAV_NEW),
             (HOME_OLD, HOME_NEW)])

print("ui upgrade patched")
