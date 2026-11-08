/*
 * Clock -- big clock for mubaiOS (installed from the app store).
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static void draw(NovaFB *fb)
{
	char clock[16], date[64];
	time_t now = time(NULL);
	struct tm tm;

	localtime_r(&now, &tm);
	snprintf(clock, sizeof(clock), "%02d:%02d", tm.tm_hour, tm.tm_min);
	snprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday,
		 (const char *[]){"日", "一", "二", "三", "四", "五", "六"}[tm.tm_wday]);

	nova_app_header(fb, "时钟");
	nova_text_center(fb, fb->w / 2, 260, clock, NOVA_WHITE, 12);
	nova_text_center(fb, fb->w / 2, 480, date, NOVA_DIM, 3);
	nova_text_center(fb, fb->w / 2, 560, "mubaiOS", 0x6c5ce7, 2);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int ptr_x = 400, ptr_y = 400;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	nova_cursor_reset();
	draw(&fb);
	nova_cursor_draw(&fb, ptr_x, ptr_y);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0) {
			nova_cursor_reset();
			draw(&fb);
			nova_cursor_draw(&fb, ptr_x, ptr_y);
			continue;
		}
		ptr_x = ev.x;
		ptr_y = ev.y;
		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;
		if (ev.type == NOVA_DOWN && nova_back_hit(ev.x, ev.y))
			return 0;
	}
}
