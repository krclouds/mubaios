/*
 * Piano -- an eight key keyboard.  mubaiOS has no audio driver yet, so this
 * demo animates the keys and the level meter instead of making sound.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static const char *names[8] = {"C", "D", "E", "F", "G", "A", "B", "C5"};
static int active = -1;
static double active_until;
static int px = 400, py = 300;

static double now_s(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec + ts.tv_nsec / 1e9;
}

static void draw(NovaFB *fb)
{
	int n = 8, kw = 130, gap = 12;
	int total = n * kw + (n - 1) * gap;
	int x0 = (fb->w - total) / 2, y0 = 300;

	nova_app_header(fb, "钢琴");
	nova_text(fb, 60, 146, "点击琴键 · 本机暂无音频驱动，仅演示交互", NOVA_DIM, 1);

	for (int i = 0; i < n; i++) {
		int x = x0 + i * (kw + gap);
		int on = (i == active && now_s() < active_until);

		nova_round_rect(fb, x, y0, kw, 300, 14, on ? 0x6c5ce7 : 0xf5f5f5);
		nova_text_center(fb, x + kw / 2, y0 + 250, names[i], on ? NOVA_WHITE : 0x1b2030, 2);
	}

	for (int i = 0; i < 18; i++) {
		int h = 20 + (i * 37 % 90);
		if (active >= 0 && now_s() < active_until)
			h = 30 + (i * 53 % 150);
		nova_fill(fb, 120 + i * 56, 680 - h, 40, h, i % 3 ? 0x2ecc71 : 0x6c5ce7);
	}
	nova_cursor_draw(fb, px, py);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int n = 8, kw = 130, gap = 12;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	nova_cursor_reset();
	draw(&fb);
	nova_cursor_draw(&fb, px, py);

	for (;;) {
		if (nova_poll(&in, &ev, 120) == 0) {
			if (active >= 0 && now_s() >= active_until) {
				active = -1;
				nova_cursor_reset();
				draw(&fb);
				nova_cursor_draw(&fb, px, py);
			}
			continue;
		}
		px = ev.x;
		py = ev.y;
		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;
		if (ev.type != NOVA_DOWN)
			continue;
		if (nova_back_hit(ev.x, ev.y))
			return 0;

		int total = n * kw + (n - 1) * gap;
		int x0 = (fb.w - total) / 2;
		if (ev.y > 300 && ev.y < 600) {
			int idx = (ev.x - x0) / (kw + gap);
			if (idx >= 0 && idx < n && ev.x >= x0) {
				active = idx;
				active_until = now_s() + 0.5;
			}
		}
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
