/*
 * Paint -- mubaiOS drawing app.
 *
 * Strokes are rasterised into an off-screen canvas that is clipped to the
 * drawing area, so nothing spills onto the header or the palette.  Each stroke
 * is stamped with round brush dabs along the segment, which gives smooth,
 * thick lines instead of the old "connect the dots" polyline.
 */
#define _GNU_SOURCE
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "nova.h"

#define CANVAS_TOP 140
#define TOOLBAR_H 104
#define BRUSH 6

static const uint32_t palette[] = {
	0xffffff, 0xe74c3c, 0xe67e22, 0xf1c40f,
	0x2ecc71, 0x3498db, 0x9b59b6, 0x1b2030,
};
#define PALETTE_N (int)(sizeof(palette) / sizeof(palette[0]))
#define CANVAS_BG 0x0f1320

static NovaFB *fb;
static uint32_t *canvas;
static uint32_t *snapshot;
static int cw, ch, canvas_bottom;
static int color_index = 1;
static int drawing;
static int last_x, last_y;
static int ptr_x = 300, ptr_y = 300;

static inline void canvas_put(int x, int y, uint32_t c)
{
	if (x < 0 || x >= cw || y < CANVAS_TOP || y >= canvas_bottom)
		return;
	canvas[(y - CANVAS_TOP) * cw + x] = c;
}

static void blit(int x0, int y0, int x1, int y1)
{
	if (x0 < 0) x0 = 0;
	if (x1 >= cw) x1 = cw - 1;
	if (y0 < CANVAS_TOP) y0 = CANVAS_TOP;
	if (y1 >= canvas_bottom) y1 = canvas_bottom - 1;

	nova_cursor_reset();
	for (int y = y0; y <= y1; y++)
		for (int x = x0; x <= x1; x++)
			nova_pixel(fb, x, y, canvas[(y - CANVAS_TOP) * cw + x]);
}

static void brush_dab(int cx, int cy, uint32_t color)
{
	for (int dy = -BRUSH; dy <= BRUSH; dy++)
		for (int dx = -BRUSH; dx <= BRUSH; dx++)
			if (dx * dx + dy * dy <= BRUSH * BRUSH)
				canvas_put(cx + dx, cy + dy, color);
}

static void stroke_segment(int x0, int y0, int x1, int y1)
{
	uint32_t color = palette[color_index];
	int dx = abs(x1 - x0), dy = abs(y1 - y0);
	int steps = dx > dy ? dx : dy;

	if (steps < 1) {
		brush_dab(x1, y1, color);
		blit(x1 - BRUSH, y1 - BRUSH, x1 + BRUSH, y1 + BRUSH);
		return;
	}
	for (int i = 0; i <= steps; i++) {
		int x = x0 + (x1 - x0) * i / steps;
		int y = y0 + (y1 - y0) * i / steps;
		brush_dab(x, y, color);
	}
	int x0b = (x0 < x1 ? x0 : x1) - BRUSH;
	int y0b = (y0 < y1 ? y0 : y1) - BRUSH;
	int x1b = (x0 > x1 ? x0 : x1) + BRUSH;
	int y1b = (y0 > y1 ? y0 : y1) + BRUSH;
	blit(x0b, y0b, x1b, y1b);
}

static void fill_canvas(uint32_t color)
{
	for (int y = CANVAS_TOP; y < canvas_bottom; y++)
		for (int x = 0; x < cw; x++)
			canvas[(y - CANVAS_TOP) * cw + x] = color;
}

static void draw_chrome(void)
{
	int y = fb->h - TOOLBAR_H;

	nova_app_header(fb, "画板");
	nova_text(fb, 60, 146, "用手指或鼠标绘制 · 可撤销", NOVA_DIM, 2);

	nova_round_rect(fb, 0, fb->h - TOOLBAR_H - 8, fb->w, TOOLBAR_H + 8, 0, 0x0b0d14);
	for (int i = 0; i < PALETTE_N; i++) {
		int cx = 70 + i * 76;
		nova_circle(fb, cx, y + 18, 24, palette[i]);
		if (i == color_index) {
			nova_circle(fb, cx, y + 18, 30, 0xffffff);
			nova_circle(fb, cx, y + 18, 24, palette[i]);
		}
	}
	nova_round_rect(fb, fb->w - 400, y + 2, 160, 48, 24, 0x2a2f40);
	nova_text_center(fb, fb->w - 320, y + 15, "撤销", NOVA_TEXT, 2);
	nova_round_rect(fb, fb->w - 220, y + 2, 160, 48, 24, 0x2a2f40);
	nova_text_center(fb, fb->w - 140, y + 15, "清空", NOVA_TEXT, 2);
}

int main(void)
{
	static NovaFB framebuffer;
	NovaInput in;
	NovaEvent ev;

	fb = &framebuffer;
	if (nova_fb_open(fb) < 0)
		return 1;
	nova_set_screen(fb->w, fb->h);

	cw = fb->w;
	canvas_bottom = fb->h - TOOLBAR_H - 8;
	ch = canvas_bottom - CANVAS_TOP;
	canvas = malloc((size_t)cw * ch * sizeof(uint32_t));
	snapshot = malloc((size_t)cw * ch * sizeof(uint32_t));
	if (!canvas || !snapshot)
		return 1;

	if (nova_input_open(&in) < 0)
		return 1;

	fill_canvas(CANVAS_BG);
	draw_chrome();
	blit(0, CANVAS_TOP, cw - 1, canvas_bottom - 1);
	nova_cursor_draw(fb, ptr_x, ptr_y);
	/* draw_chrome() repaints the whole screen, so the canvas is blitted after it */

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		ptr_x = ev.x;
		ptr_y = ev.y;

		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;

		if (ev.type == NOVA_MOVE) {
			if (drawing) {
				stroke_segment(last_x, last_y, ev.x, ev.y);
				last_x = ev.x;
				last_y = ev.y;
			} else {
				nova_cursor_draw(fb, ev.x, ev.y);
			}
			continue;
		}

		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y))
				return 0;
			if (ev.y >= fb->h - TOOLBAR_H) {
				if (ev.x > fb->w - 240) {
					fill_canvas(CANVAS_BG);
				} else if (ev.x > fb->w - 420) {
					memcpy(canvas, snapshot, (size_t)cw * ch * sizeof(uint32_t));
				} else {
					int idx = (ev.x - 40) / 76;
					if (idx >= 0 && idx < PALETTE_N)
						color_index = idx;
				}
				draw_chrome();
				blit(0, CANVAS_TOP, cw - 1, canvas_bottom - 1);
				nova_cursor_draw(fb, ev.x, ev.y);
				continue;
			}
			if (ev.y < CANVAS_TOP)
				continue;
			memcpy(snapshot, canvas, (size_t)cw * ch * sizeof(uint32_t));
			drawing = 1;
			last_x = ev.x;
			last_y = ev.y;
			stroke_segment(ev.x, ev.y, ev.x, ev.y);
		} else if (ev.type == NOVA_UP) {
			if (drawing) {
				drawing = 0;
				nova_cursor_draw(fb, ev.x, ev.y);
			}
		}
	}
}
