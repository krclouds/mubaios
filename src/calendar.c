/*
 * Calendar -- a month grid for mubaiOS.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static int year, month;   /* month 1..12 */
static int px = 400, py = 300;

static int days_in(int y, int m)
{
	static const int d[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
	int leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;

	return d[m - 1] + (m == 2 && leap);
}

static void draw(NovaFB *fb)
{
	time_t now = time(NULL);
	struct tm tm;
	int first, today = 0;
	char buf[64];

	localtime_r(&now, &tm);
	if (year == 0) {
		year = tm.tm_year + 1900;
		month = tm.tm_mon + 1;
	}
	if (year == tm.tm_year + 1900 && month == tm.tm_mon + 1)
		today = tm.tm_mday;

	nova_app_header(fb, "日历");
	snprintf(buf, sizeof(buf), L("%d年%d月", "%d/%d"), year, month);
	nova_text_center(fb, fb->w / 2, 160, buf, NOVA_WHITE, 3);

	nova_round_rect(fb, 120, 210, 90, 60, 14, 0x2a2f40);
	nova_text_center(fb, 165, 228, "<", NOVA_WHITE, 3);
	nova_round_rect(fb, fb->w - 210, 210, 90, 60, 14, 0x2a2f40);
	nova_text_center(fb, fb->w - 165, 228, ">", NOVA_WHITE, 3);

	const char *wd[7] = {"日", "一", "二", "三", "四", "五", "六"};
	int x0 = 160, y0 = 300, cw = 137, ch = 78;

	for (int i = 0; i < 7; i++)
		nova_text_center(fb, x0 + i * cw + cw / 2, y0 - 40, wd[i], NOVA_DIM, 2);

	struct tm first_tm = {0};
	first_tm.tm_year = year - 1900;
	first_tm.tm_mon = month - 1;
	first_tm.tm_mday = 1;
	mktime(&first_tm);
	first = first_tm.tm_wday;

	int n = days_in(year, month);
	for (int d = 1; d <= n; d++) {
		int cell = first + d - 1;
		int col = cell % 7, row = cell / 7;
		int x = x0 + col * cw, y = y0 + row * ch;

		if (d == today)
			nova_round_rect(fb, x + 8, y + 4, cw - 16, ch - 12, 12, 0x6c5ce7);
		snprintf(buf, sizeof(buf), "%d", d);
		nova_text_center(fb, x + cw / 2, y + 16, buf, d == today ? NOVA_WHITE : NOVA_TEXT, 2);
	}
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
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;
		if (ev.type != NOVA_DOWN)
			continue;
		if (nova_back_hit(ev.x, ev.y))
			return 0;
		if (nova_hit(ev.x, ev.y, 120, 210, 90, 60)) {
			if (--month < 1) {
				month = 12;
				year--;
			}
		} else if (nova_hit(ev.x, ev.y, fb.w - 210, 210, 90, 60)) {
			if (++month > 12) {
				month = 1;
				year++;
			}
		}
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
