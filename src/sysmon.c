/*
 * System Monitor -- load, memory and uptime from /proc.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "nova.h"

static int px = 400, py = 300;

static void read_mem(unsigned long *total, unsigned long *avail)
{
	FILE *f = fopen("/proc/meminfo", "r");
	char key[64], line[256];
	unsigned long v;

	*total = *avail = 0;
	if (!f)
		return;
	while (fgets(line, sizeof(line), f)) {
		if (sscanf(line, "%63[^:]: %lu", key, &v) != 2)
			continue;
		if (strcmp(key, "MemTotal") == 0)
			*total = v;
		else if (strcmp(key, "MemAvailable") == 0)
			*avail = v;
	}
	fclose(f);
}

static void bar(NovaFB *fb, int x, int y, int w, double ratio, uint32_t color)
{
	if (ratio < 0)
		ratio = 0;
	if (ratio > 1)
		ratio = 1;
	nova_round_rect(fb, x, y, w, 28, 8, 0x232838);
	nova_round_rect(fb, x, y, (int)(w * ratio), 28, 8, color);
}

static void draw(NovaFB *fb)
{
	char line[128];
	double load[3] = {0, 0, 0};
	unsigned long total = 0, avail = 0;
	double up = 0;

	nova_app_header(fb, "系统监视");
	FILE *f = fopen("/proc/loadavg", "r");
	if (f) {
		if (fscanf(f, "%lf %lf %lf", &load[0], &load[1], &load[2]) != 3)
			load[0] = load[1] = load[2] = 0;
		fclose(f);
	}
	f = fopen("/proc/uptime", "r");
	if (f) {
		if (fscanf(f, "%lf", &up) != 1)
			up = 0;
		fclose(f);
	}
	read_mem(&total, &avail);

	snprintf(line, sizeof(line), L("运行时间 %.0f 分 %.0f 秒", "Uptime %.0f min %.0f s"), up / 60, (double)((long)up % 60));
	nova_text(fb, 80, 190, line, NOVA_TEXT, 2);

	nova_text(fb, 80, 260, L("负载 (1/5/15 分钟)", "Load (1/5/15 min)"), NOVA_DIM, 2);
	snprintf(line, sizeof(line), "%.2f   %.2f   %.2f", load[0], load[1], load[2]);
	nova_text(fb, 80, 300, line, NOVA_WHITE, 3);

	nova_text(fb, 80, 400, "内存", NOVA_DIM, 2);
	snprintf(line, sizeof(line), "%.0f MB / %.0f MB", (total - avail) / 1024.0, total / 1024.0);
	nova_text(fb, 80, 436, line, NOVA_TEXT, 2);
	bar(fb, 80, 480, fb->w - 240, total ? 1.0 - (double)avail / total : 0, NOVA_OK);

	nova_text(fb, 80, 550, L("CPU 核心", "CPU cores"), NOVA_DIM, 2);
	snprintf(line, sizeof(line), "%ld", sysconf(_SC_NPROCESSORS_ONLN));
	nova_text(fb, 80, 586, line, NOVA_TEXT, 2);

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
		if (nova_poll(&in, &ev, 500) == 0) {
			nova_cursor_reset();
			draw(&fb);
			nova_cursor_draw(&fb, px, py);
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
		if (ev.type == NOVA_DOWN && nova_back_hit(ev.x, ev.y))
			return 0;
	}
}
