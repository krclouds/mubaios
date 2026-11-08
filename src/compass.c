/*
 * Compass -- drag to rotate, the needle always points to the cached heading.
 */
#define _GNU_SOURCE
#include <math.h>
#include <stdio.h>
#include <unistd.h>

#include "nova.h"

static double heading = 45;
static int dragging, last_x;
static int px = 400, py = 300;

static void draw(NovaFB *fb)
{
	int cx = fb->w / 2, cy = 430, r = 220;
	const char *dirs[4] = {"北", "东", "南", "西"};

	nova_app_header(fb, "指南针");
	nova_circle(fb, cx, cy, r + 14, 0x232838);
	nova_circle(fb, cx, cy, r, 0x141821);
	nova_circle(fb, cx, cy, 8, 0x6c5ce7);

	for (int i = 0; i < 4; i++) {
		double a = (i * 90 - heading) * M_PI / 180.0;
		int tx = cx + (int)(sin(a) * (r - 40));
		int ty = cy - (int)(cos(a) * (r - 40));

		nova_text_center(fb, tx, ty - 16, dirs[i], i == 0 ? 0xe74c3c : NOVA_TEXT, 2);
	}
	for (int i = 0; i < 36; i++) {
		double a = (i * 10 - heading) * M_PI / 180.0;
		int x0 = cx + (int)(sin(a) * (r - 12));
		int y0 = cy - (int)(cos(a) * (r - 12));
		int x1 = cx + (int)(sin(a) * (r - 2));
		int y1 = cy - (int)(cos(a) * (r - 2));

		nova_line(fb, x0, y0, x1, y1, (i % 9 == 0) ? NOVA_WHITE : 0x3a3f55);
	}

	double a = -heading * M_PI / 180.0;
	nova_line(fb, cx, cy, cx + (int)(sin(a) * (r - 60)), cy - (int)(cos(a) * (r - 60)), 0xe74c3c);
	nova_line(fb, cx, cy, cx - (int)(sin(a) * 90), cy + (int)(cos(a) * 90), 0x9aa0b5);

	char buf[32];
	snprintf(buf, sizeof(buf), "%d°", (int)heading);
	nova_text_center(fb, cx, 170, buf, NOVA_WHITE, 4);
	nova_text_center(fb, cx, 700, "左右拖动旋转表盘", NOVA_DIM, 1);
	nova_cursor_draw(fb, px, py);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	nova_cursor_reset();
	draw(&fb);
	nova_cursor_draw(&fb, px, py);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		px = ev.x;
		py = ev.y;

		if (ev.type == NOVA_MOVE) {
			if (dragging) {
				heading += (ev.x - last_x) * 0.5;
				while (heading < 0)
					heading += 360;
				while (heading >= 360)
					heading -= 360;
				last_x = ev.x;
				nova_cursor_reset();
				draw(&fb);
			}
			nova_cursor_draw(&fb, px, py);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;
		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y))
				return 0;
			dragging = 1;
			last_x = ev.x;
		} else if (ev.type == NOVA_UP) {
			dragging = 0;
		}
	}
}
