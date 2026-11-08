/*
 * Weather -- an offline five day forecast (demo data, refreshed locally).
 */
#define _GNU_SOURCE
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static const char *days[5] = {"今天", "明天", "第三天", "第四天", "第五天"};
static const char *conds[5] = {"晴", "多云", "小雨", "阴", "晴"};
static int temps[5] = {21, 19, 16, 18, 23};
static int px = 400, py = 300;

static void draw_sun(NovaFB *fb, int x, int y, int r, uint32_t c)
{
	nova_circle(fb, x, y, r, c);
	for (int i = 0; i < 8; i++) {
		double a = i * M_PI / 4;

		nova_line(fb, x + (int)(sin(a) * (r + 4)), y - (int)(cos(a) * (r + 4)),
			  x + (int)(sin(a) * (r + 12)), y - (int)(cos(a) * (r + 12)), c);
	}
}

static void draw(NovaFB *fb)
{
	nova_app_header(fb, "天气");
	nova_text(fb, 80, 150, "北京", NOVA_WHITE, 3);
	nova_text(fb, 80, 200, "演示数据 · 无网络", NOVA_DIM, 1);

	draw_sun(fb, 980, 210, 46, 0xf1c40f);
	char buf[32];
	snprintf(buf, sizeof(buf), "%d°C", temps[0]);
	nova_text(fb, 80, 240, buf, NOVA_WHITE, 8);

	for (int i = 0; i < 5; i++) {
		int x = 70 + i * 226;
		nova_round_rect(fb, x, 400, 206, 250, 18, 0x1b2030);
		nova_text_center(fb, x + 103, 424, days[i], NOVA_DIM, 1);
		nova_circle(fb, x + 103, 500, 30, i == 2 ? 0x7f8c8d : 0xf1c40f);
		nova_text_center(fb, x + 103, 552, conds[i], NOVA_TEXT, 2);
		snprintf(buf, sizeof(buf), "%d°", temps[i]);
		nova_text_center(fb, x + 103, 600, buf, NOVA_WHITE, 3);
	}
	nova_round_rect(fb, fb->w / 2 - 120, 690, 240, 64, 18, 0x2a2f40);
	nova_text_center(fb, fb->w / 2, 706, "刷新", NOVA_WHITE, 2);
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

	srand((unsigned)time(NULL));
	nova_cursor_reset();
	draw(&fb);
	nova_cursor_draw(&fb, px, py);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
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
		if (nova_hit(ev.x, ev.y, fb.w / 2 - 120, 690, 240, 64))
			for (int i = 0; i < 5; i++)
				temps[i] = 12 + rand() % 14;
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
