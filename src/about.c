/*
 * About -- system information.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <sys/utsname.h>
#include <unistd.h>

#include "nova.h"

static void read_line(const char *path, char *buf, size_t n)
{
	FILE *f = fopen(path, "r");

	buf[0] = 0;
	if (f) {
		if (fgets(buf, (int)n, f))
			buf[strcspn(buf, "\n")] = 0;
		fclose(f);
	}
}

static void draw(NovaFB *fb)
{
	struct utsname u;
	char line[128];
	int y = 200;

	uname(&u);
	nova_app_header(fb, "关于");
	nova_round_rect(fb, 60, 160, fb->w - 120, 120, 18, 0x1b2030);
	nova_text(fb, 92, 180, "mubaiOS 0.1", NOVA_WHITE, 3);
	nova_text(fb, 92, 228, "自研用户态 + Linux 内核的桌面系统", NOVA_DIM, 1);

	const char *labels[6] = {"内核", "架构", "分辨率", "内存", "根文件系统", "应用"};
	char values[6][128];

	snprintf(values[0], sizeof(values[0]), "%s %s", u.sysname, u.release);
	snprintf(values[1], sizeof(values[1]), "%s", u.machine);
	snprintf(values[2], sizeof(values[2]), "%dx%d %d bpp", fb->w, fb->h, fb->bpp);
	read_line("/proc/meminfo", line, sizeof(line));
	snprintf(values[3], sizeof(values[3]), "%s", line);
	snprintf(values[4], sizeof(values[4]), "initramfs（内存）");
	snprintf(values[5], sizeof(values[5]), "4 个预装 + 应用商店");

	for (int i = 0; i < 6; i++) {
		nova_text(fb, 80, y, labels[i], NOVA_DIM, 2);
		nova_text(fb, 360, y, values[i], NOVA_TEXT, 2);
		y += 48;
	}
	nova_text(fb, 80, fb->h - 90, "基于 Linux 内核，用户态全部自研", 0x4a5068, 1);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int px = 400, py = 300;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

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
		if (ev.type == NOVA_DOWN && nova_back_hit(ev.x, ev.y))
			return 0;
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
