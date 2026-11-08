/*
 * system_server -- the mubaiOS shell.
 *
 * Draws the status bar, the home screen and the navigation bar, scans /apps
 * for installed applications, and runs a tapped app as a child process.  When
 * the app exits the home screen comes back.  This is the whole "desktop" of
 * mubaiOS: no Wayland, no X11, no toolkit -- just /dev/fb0 and /dev/input.
 */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <math.h>
#include <time.h>
#include <linux/input.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include "nova.h"

#define MAX_APPS 12
#define ICON 132
#define GAPX 64
#define GAPY 84

struct app {
	char id[32];
	char name[48];
	char icon[8];
	uint32_t color;
	int order;
};

static struct app apps[MAX_APPS];
static int app_count;
static int scroll_y;

static void parse_manifest(const char *path, struct app *a)
{
	FILE *f = fopen(path, "r");
	char line[256];

	if (!f)
		return;
	while (fgets(line, sizeof(line), f)) {
		char *eq = strchr(line, '=');
		char *nl;
		if (!eq)
			continue;
		*eq = '\0';
		char *v = eq + 1;
		nl = strchr(v, '\n');
		if (nl)
			*nl = '\0';
		if (strcmp(line, "name") == 0)
			snprintf(a->name, sizeof(a->name), "%s", v);
		else if (strcmp(line, "icon") == 0)
			snprintf(a->icon, sizeof(a->icon), "%s", v);
		else if (strcmp(line, "color") == 0)
			a->color = (uint32_t)strtoul(v, NULL, 16);
		else if (strcmp(line, "order") == 0)
			a->order = atoi(v);
	}
	fclose(f);
}

static void scan_apps(void)
{
	DIR *dir;

	app_count = 0;
	dir = opendir("/apps");
	struct dirent *de;

	if (!dir)
		return;
	while ((de = readdir(dir)) && app_count < MAX_APPS) {
		char path[256];
		struct app *a;

		if (de->d_name[0] == '.')
			continue;
		snprintf(path, sizeof(path), "/apps/%s/manifest", de->d_name);
		if (access(path, R_OK) != 0)
			continue;
		a = &apps[app_count];
		memset(a, 0, sizeof(*a));
		snprintf(a->id, sizeof(a->id), "%s", de->d_name);
		snprintf(a->name, sizeof(a->name), "%s", de->d_name);
		snprintf(a->icon, sizeof(a->icon), "%s", "?");
		a->color = NOVA_ACCENT;
		a->order = 100 + app_count;
		parse_manifest(path, a);
		app_count++;
	}
	closedir(dir);

	/* insertion sort by manifest order */
	for (int i = 1; i < app_count; i++) {
		struct app key = apps[i];
		int j = i - 1;
		while (j >= 0 && apps[j].order > key.order) {
			apps[j + 1] = apps[j];
			j--;
		}
		apps[j + 1] = key;
	}
}

static void grid_geometry(int w, int *x0, int *y0, int *cols)
{
	int total = 4 * ICON + 3 * GAPX;

	*cols = 4;
	*x0 = (w - total) / 2;
	*y0 = 222;
}



static int max_scroll(NovaFB *fb)
{
	int x0, y0, cols, rows, content, view;

	grid_geometry(fb->w, &x0, &y0, &cols);
	rows = (app_count + cols - 1) / cols;
	content = y0 + rows * (ICON + GAPY) - GAPY + ICON;
	view = fb->h - NOVA_NAVBAR_H - 20;
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


/* ---------------- Material-ish shell pieces ---------------- */

static int shade;
static int paused;
static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover);
static void cursor_hide(NovaFB *fb);
                 /* 0 = closed, 1 = open */
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

static void shell_status_bar(NovaFB *fb, const char *clock, const char *date)
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
	nova_text(fb, x + 68, y + 19, "搜索应用", fg, 2);
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


static void tile_glyph(NovaFB *fb, int i, int cx, int cy, uint32_t fg, uint32_t bg)
{
	if (i == 0) {			/* wifi */
		nova_circle(fb, cx, cy + 7, 4, fg);
		nova_line(fb, cx - 7, cy - 2, cx, cy - 8, fg);
		nova_line(fb, cx, cy - 8, cx + 7, cy - 2, fg);
		nova_line(fb, cx - 12, cy - 8, cx, cy - 17, fg);
		nova_line(fb, cx, cy - 17, cx + 12, cy - 8, fg);
	} else if (i == 1) {		/* bluetooth */
		nova_line(fb, cx, cy - 15, cx, cy + 15, fg);
		nova_line(fb, cx, cy - 15, cx + 9, cy - 7, fg);
		nova_line(fb, cx + 9, cy - 7, cx - 8, cy + 6, fg);
		nova_line(fb, cx, cy + 15, cx + 9, cy + 7, fg);
		nova_line(fb, cx + 9, cy + 7, cx - 8, cy - 6, fg);
	} else if (i == 2) {		/* moon */
		nova_circle(fb, cx - 3, cy - 1, 14, fg);
		nova_circle(fb, cx + 7, cy - 6, 12, bg);
	} else if (i == 3) {		/* plane */
		nova_line(fb, cx - 14, cy + 8, cx + 15, cy - 4, fg);
		nova_line(fb, cx - 2, cy - 14, cx + 15, cy - 4, fg);
		nova_line(fb, cx - 9, cy + 1, cx - 2, cy - 14, fg);
	} else if (i == 4) {		/* flashlight */
		nova_round_rect(fb, cx - 6, cy - 4, 12, 20, 4, fg);
		nova_round_rect(fb, cx - 10, cy - 15, 20, 9, 3, fg);
		nova_fill(fb, cx - 14, cy - 19, 3, 14, fg);
		nova_fill(fb, cx + 11, cy - 19, 3, 14, fg);
	} else {			/* rotate */
		for (int k = 0; k < 9; k++) {
			float a = (float)k * 0.7f;
			int px = cx + (int)(13 * cosf(a));
			int py = cy + (int)(13 * sinf(a));

			nova_circle(fb, px, py, 3, fg);
		}
		nova_circle(fb, cx, cy, 5, fg);
	}
}

static void shade_tile_rect(NovaFB *fb, int i, int *x, int *y, int *w, int *h)
{
	int cols = 3, gap = 16, x0 = 56;
	int tw = (fb->w - 2 * x0 - (cols - 1) * gap) / cols;

	*w = tw;
	*h = 96;
	*x = x0 + (i % cols) * (tw + gap);
	*y = 150 + (i / cols) * (96 + gap);
}

static void draw_shade(NovaFB *fb)
{
	static const char *labels[6] = {
		"无线网络", "蓝牙", "勿扰模式",
		"飞行模式", "手电筒", "自动旋转"
	};

	nova_round_rect_blend(fb, 0, 0, fb->w, fb->h, 0, 0x05060c, 130);
	nova_round_rect_gradient(fb, 0, 0, fb->w, 604, 36, 0x1c2238, 0x111527);
	nova_text(fb, 56, 58, "mubaiOS", NOVA_WHITE, 3);
	nova_text(fb, 56, 104, "快捷设置", 0x8f96ad, 2);
	{
		char now[8];
		int nw;

		nova_clock(now, sizeof(now));
		nw = nova_text_width(now, 3);
		nova_text_shadow(fb, fb->w - 56 - nw, 58, now, NOVA_WHITE, 3);
	}

	for (int i = 0; i < 6; i++) {
		int x, y, w, h;

		shade_tile_rect(fb, i, &x, &y, &w, &h);
		nova_round_rect(fb, x, y, w, h, 26, tile_on[i] ? 0x2f3a63 : 0x1a2032);
		nova_circle(fb, x + 40, y + 34, 21, tile_on[i] ? 0xa9b6ff : 0x3a4160);
		tile_glyph(fb, i, x + 40, y + 34, tile_on[i] ? 0x2f3a63 : 0x232a40,
			   tile_on[i] ? 0xa9b6ff : 0x3a4160);
		nova_text(fb, x + 24, y + 60, labels[i], tile_on[i] ? NOVA_WHITE : 0x9aa0b5, 2);
	}

	/* brightness slider */
	nova_text(fb, 56, 396, "亮度", 0x9aa0b5, 2);
	nova_round_rect(fb, 56, 430, fb->w - 112, 26, 13, 0x1a2032);
	nova_round_rect(fb, 56, 430, (fb->w - 112) * 68 / 100, 26, 13, 0x6c5ce7);
	nova_circle(fb, 56 + (fb->w - 112) * 68 / 100, 443, 19, 0xffffff);

	nova_round_rect(fb, 56, 486, fb->w - 112, 86, 24, 0x232a3e);
	nova_circle(fb, 94, 516, 15, 0x3a4160);
	nova_text(fb, 124, 496, "没有通知", NOVA_WHITE, 2);
	nova_text(fb, 124, 530, "mubaiOS 0.1", 0x8f96ad, 2);
}

static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover)
{
	uint32_t top = nova_mix(a->color, 0xffffff, 40);
	uint32_t bottom = nova_mix(a->color, 0x05060c, 84);
	int nw;

	if (hover)
		nova_round_rect(fb, x - 9, y - 9, ICON + 18, ICON + 18, 44, 0x272d47);
	nova_shadow(fb, x, y + 5, ICON, ICON, 34, 4, 110);
	nova_squircle(fb, x, y, ICON, ICON, top, bottom);

	app_glyph(fb, a, x + ICON / 2, y + ICON / 2, ICON * 82 / 100, NOVA_WHITE, bottom);

	nw = nova_text_width(a->name, 2);
	nova_text(fb, x + (ICON - nw) / 2 + 1, y + ICON + 13, a->name, 0x05060c, 2);
	nova_text(fb, x + (ICON - nw) / 2, y + ICON + 12, a->name, 0xe8eaf6, 2);
}

static uint32_t *wall_buf;
static uint32_t cursor_bg[24 * 24];
static int cursor_bg_x, cursor_bg_y, cursor_bg_valid;

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
	cursor_hide(fb);
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
	nova_mark_clean();
}

static void cursor_hide(NovaFB *fb)
{
	if (!cursor_bg_valid)
		return;
	for (int dy = 0; dy < 24; dy++)
		for (int dx = 0; dx < 24; dx++) {
			int px = cursor_bg_x + dx, py = cursor_bg_y + dy;

			if (px >= 0 && py >= 0 && px < fb->w && py < fb->h)
				nova_pixel(fb, px, py, cursor_bg[dy * 24 + dx]);
		}
	cursor_bg_valid = 0;
}

static void draw_nav(NovaFB *fb, int hover_back, int hover_home, int hover_recent)
{
	int y = fb->h - NOVA_NAVBAR_H;

	nova_fill(fb, 0, y, fb->w, NOVA_NAVBAR_H, 0x0b0d14);
	nova_fill(fb, 0, y, fb->w, 2, 0x232838);

	int cx = fb->w / 2;
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
	nova_round_rect(fb, cx - 60, fb->h - 13, 120, 5, 3, 0x2c3350);
}


static void draw_cursor(NovaFB *fb, int x, int y)
{
	int was_dirty = nova_dirty();
	int old_x = cursor_bg_x, old_y = cursor_bg_y, had_bg = cursor_bg_valid;
	if (cursor_bg_valid) {
		for (int dy = 0; dy < 24; dy++)
			for (int dx = 0; dx < 24; dx++) {
				int px = cursor_bg_x + dx, py = cursor_bg_y + dy;
				if (px >= 0 && py >= 0 && px < fb->w && py < fb->h)
					nova_pixel(fb, px, py, cursor_bg[dy * 24 + dx]);
			}
		cursor_bg_valid = 0;
	}
	for (int dy = 0; dy < 24; dy++)
		for (int dx = 0; dx < 24; dx++) {
			int px = x - 9 + dx, py = y - 9 + dy;
			cursor_bg[dy * 24 + dx] = nova_get(fb, px, py);
		}
	cursor_bg_x = x - 9;
	cursor_bg_y = y - 9;
	cursor_bg_valid = 1;
	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
	if (was_dirty) {
		nova_flush(fb);
	} else {
		if (had_bg)
			nova_flush_rect(fb, old_x, old_y, 24, 24);
		nova_flush_rect(fb, x - 9, y - 9, 24, 24);
	}
}

static uint32_t *wall_buf;
static size_t wall_len;

static void build_wallpaper(NovaFB *fb)
{
	size_t n = (size_t)fb->w * fb->h;

	wall_buf = malloc(n * 4);
	wall_len = wall_buf ? n : 0;
	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x1d1746, 0x05050d);
	nova_glow(fb, fb->w - 60, 40, 470, 0x8b5cff, 170);
	nova_glow(fb, 40, fb->h - 40, 430, 0x2f7bff, 130);
	nova_glow(fb, fb->w / 2 + 200, fb->h / 2 - 40, 520, 0xc44cff, 90);
	nova_glow(fb, fb->w - 200, fb->h - 120, 300, 0x36d1dc, 60);
	for (int yy = fb->h - 260; yy < fb->h; yy++) {
		int a = 140 * (yy - (fb->h - 260)) / 260;

		for (int xx = 0; xx < fb->w; xx++)
			nova_blend_px(fb, xx, yy, 0x05060c, a);
	}
	if (wall_buf)
		memcpy(wall_buf, fb->buf, n * 4);
}

static void draw_scroll_region(NovaFB *fb, int hover)
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
	nova_mark_clean();
}

static void draw_status_only(NovaFB *fb, const char *clk)
{
	if (shade)
		return;

	char date[64];
	time_t now = time(NULL);
	struct tm tm;

	localtime_r(&now, &tm);
	if (nova_lang()) {
		strftime(date, sizeof(date), "%a, %d %b", &tm);
	} else {
		static const char *wd[] = {"日", "一", "二", "三", "四", "五", "六"};
		snprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday, wd[tm.tm_wday]);
	}

	cursor_hide(fb);
	shell_status_bar(fb, clk, date);
	cursor_bg_valid = 0;
	cursor_hide(fb);
	nova_flush_rect(fb, 0, 0, fb->w, 56);
	nova_mark_clean();
}

static void draw_home(NovaFB *fb, int cursor_x, int cursor_y, int hover)
{
	char clock[16], date[64];
	time_t now = time(NULL);
	struct tm tm;

	localtime_r(&now, &tm);
	strftime(clock, sizeof(clock), "%H:%M", &tm);
	if (nova_lang()) {
		strftime(date, sizeof(date), "%a, %d %b", &tm);
	} else {
		static const char *wd[] = {"日", "一", "二", "三", "四", "五", "六"};
		snprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday, wd[tm.tm_wday]);
	}

	if (!wall_buf)
		build_wallpaper(fb);
	else
		memcpy(fb->buf, wall_buf, wall_len * 4);

	if (!shade)
		shell_status_bar(fb, clock, date);
	nova_text(fb, 56, 78, "欢迎回来", NOVA_WHITE, 3);
	draw_search(fb, 140);

	int x0, y0, cols;
	grid_geometry(fb->w, &x0, &y0, &cols);
	for (int i = 0; i < app_count; i++) {
		int col = i % cols;
		int row = i / cols;
		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY) - scroll_y;

		if (y < 204 || y > fb->h - NOVA_NAVBAR_H)
			continue;
		draw_icon(fb, x, y, &apps[i], i == hover);
	}
	{
		int ms = max_scroll(fb);

		if (ms > 0) {
			int top = 150, bot = fb->h - NOVA_NAVBAR_H - 18;
			int h = (bot - top) * (bot - top) / ((bot - top) + ms);
			int ty = top + (bot - top - h) * scroll_y / ms;

			nova_round_rect_blend(fb, fb->w - 22, ty, 5, h, 3, 0xdfe3f5, 90);
		}
	}
	if (app_count == 0)
		nova_text(fb, 60, 320, "No applications installed in /apps", NOVA_DIM, 2);

	draw_dock(fb);
	if (shade)
		draw_shade(fb);
	cursor_bg_valid = 0;
	nova_flush(fb);
	draw_cursor(fb, cursor_x, cursor_y);
}

static int hit_icon(NovaFB *fb, int mx, int my)
{
	int x0, y0, cols;

	grid_geometry(fb->w, &x0, &y0, &cols);
	for (int i = 0; i < app_count; i++) {
		int col = i % cols, row = i / cols;
		int x = x0 + col * (ICON + GAPX);
		int y = y0 + row * (ICON + GAPY) - scroll_y;

		if (y < 204 || y > fb->h - NOVA_NAVBAR_H)
			continue;
		if (nova_hit(mx, my, x - 6, y - 6, ICON + 12, ICON + 12))
			return i;
	}
	return -1;
}

static int hit_nav(NovaFB *fb, int mx, int my)
{
	int y = fb->h - NOVA_NAVBAR_H;
	int cx = fb->w / 2;

	if (my < y)
		return -1;
	if (nova_hit(mx, my, cx - 190, y, 80, NOVA_NAVBAR_H))
		return 1; /* back */
	if (nova_hit(mx, my, cx - 40, y, 80, NOVA_NAVBAR_H))
		return 2; /* home */
	if (nova_hit(mx, my, cx + 130, y, 80, NOVA_NAVBAR_H))
		return 3; /* recents */
	return -1;
}

static void ripple_at(NovaFB *fb, int cx, int cy)
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

static void launch_app(const struct app *a)
{
	char path[128];
	pid_t pid;

	snprintf(path, sizeof(path), "/apps/%s/%s", a->id, a->id);
	fprintf(stderr, "system_server: launching %s\n", path);

	pid = fork();
	if (pid == 0) {
		execl(path, path, (char *)NULL);
		_exit(127);
	}
	if (pid < 0)
		return;
	waitpid(pid, NULL, 0);
	/* the store may have installed or removed apps, and Settings may have
	 * changed the language while it ran */
	nova_lang_reload();
	scan_apps();
}


static int upgrade_pointer(NovaInput *in)
{
	NovaInput probe;

	if (!in->abs_virtual)
		return 0;
	if (nova_input_open(&probe) != 0)
		return 0;
	if (probe.abs_fd >= 0 && !probe.abs_virtual) {
		char nm[80] = {0};

		nova_input_close(in);
		*in = probe;
		ioctl(in->abs_fd, EVIOCGNAME(sizeof(nm)), nm);
		fprintf(stderr, "system_server: pointer switched to %s\n", nm);
		return 1;
	}
	nova_input_close(&probe);
	return 0;
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int hover = -1, pressed = -1, nav_pressed = -1;
	int pressing = 0, dragged = 0, drag_y = 0, drag_scroll = 0;
	char clock[16];
	time_t last_clock = 0;

	if (nova_fb_open(&fb) < 0) {
		fprintf(stderr, "system_server: no framebuffer\n");
		return 1;
	}
	nova_set_screen(fb.w, fb.h);
	{
		int bound = 0;

		/* The USB tablet shows up a few hundred ms after inputd creates its
		 * virtual touchscreen.  Wait for the real one, otherwise the desktop
		 * would listen to the injection device and ignore the mouse. */
		for (int attempt = 0; attempt < 150; attempt++) {
			int rc = nova_input_open(&in);

			if (rc == 0) {
				if (in.abs_fd >= 0 && !in.abs_virtual) {
					bound = 1;
					break;
				}
			}
			nova_input_close(&in);
			usleep(100000);
		}
		if (!bound) {
			nova_input_close(&in);
			nova_input_open(&in);
		}
	}
	if (in.nfds == 0)
		fprintf(stderr, "system_server: no input devices, running blind\n");

	scan_apps();
	{
		char nm[80] = {0};

		if (in.abs_fd >= 0)
			ioctl(in.abs_fd, EVIOCGNAME(sizeof(nm)), nm);
		fprintf(stderr, "system_server: %d apps, screen %dx%d, pointer=%s\n",
			app_count, fb.w, fb.h, nm[0] ? nm : "(none)");
	}

	draw_home(&fb, in.x, in.y, hover);
	fputs("SYSTEMUI_READY\n", stderr);

	for (;;) {
		/* Minecraft owns the framebuffer while /run/mc_mode exists; the
		 * desktop stays alive but stops painting so it cannot fight X. */
		if (access("/run/mc_mode", F_OK) == 0) {
			paused = 1;
			usleep(60000);
			continue;
		}
		if (paused) {
			paused = 0;
			nova_cursor_reset();
			draw_home(&fb, 640, 400, -1);
		}
		if (nova_poll(&in, &ev, 250) == 0) {
			time_t now = time(NULL);

			upgrade_pointer(&in);
			if (now != last_clock) {
				char fresh[16];

				last_clock = now;
				nova_clock(fresh, sizeof(fresh));
				if (strcmp(fresh, clock) != 0) {
					memcpy(clock, fresh, sizeof(clock));
					draw_status_only(&fb, clock);
				}
			}
			continue;
		}

		switch (ev.type) {
		case NOVA_MOVE: {
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
			h = hit_icon(&fb, ev.x, ev.y);

			if (h != hover) {
				int old = hover;

				hover = h;
				if (old >= 0)
					repaint_icon(&fb, old, hover);
				if (h >= 0)
					repaint_icon(&fb, h, hover);
			}
			draw_cursor(&fb, ev.x, ev.y);
			break;
		}
		case NOVA_DOWN:
			pressing = 1;
			dragged = 0;
			drag_y = ev.y;
			drag_scroll = scroll_y;
			pressed = hit_icon(&fb, ev.x, ev.y);
			if (pressed < 0 && dock_hit(&fb, ev.x, ev.y) >= 0)
				pressed = -2;
			nav_pressed = hit_nav(&fb, ev.x, ev.y);
			break;
		case NOVA_WHEEL:
			scroll_y = clamp_scroll(&fb, scroll_y - ev.value * 70);
			draw_home(&fb, ev.x, ev.y, hover);
			break;
		case NOVA_UP: {
			int idx, nav;

			pressing = 0;
			if (dragged) {
				dragged = 0;
				pressed = -1;
				nav_pressed = -1;
				break;
			}
			if (shade) {
				int hit = -1;

				for (int i = 0; i < 6; i++) {
					int tx, ty, tw, th;

					shade_tile_rect(&fb, i, &tx, &ty, &tw, &th);
					if (nova_hit(ev.x, ev.y, tx, ty, tw, th))
						hit = i;
				}
				if (hit >= 0) {
					tile_on[hit] = !tile_on[hit];
				} else if (ev.y > 604) {
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
			}
			if (nav == 3) {
				nova_fill(&fb, 0, 0, fb.w, fb.h, 0x000000);
				nova_text_center(&fb, fb.w / 2, fb.h / 2, "没有最近的应用", NOVA_DIM, 3);
				nova_poll(&in, &ev, 1200);
				draw_home(&fb, ev.x, ev.y, hover);
			} else if (nav == 2) {
				draw_home(&fb, ev.x, ev.y, hover);
			} else if (idx >= 0 && idx == pressed) {
				fprintf(stderr, "launch index=%d pressed=%d\n", idx, pressed);
				launch_app(&apps[idx]);
				draw_home(&fb, ev.x, ev.y, hover);
			} else {
				draw_home(&fb, ev.x, ev.y, hover);
			}
			pressed = -1;
			nav_pressed = -1;
			break;
		}
		case NOVA_KEY:
			if (ev.key == 1) { /* ESC returns to home */
				shade = 0;
				draw_home(&fb, ev.x, ev.y, hover);
			}
			break;
		default:
			break;
		}
	}
}
