/*
 * Settings -- a mubaiOS app.
 *
 * Shows device information read straight from the kernel (/proc, uname) and
 * lets the user power the machine off.  Every app in mubaiOS is a standalone
 * ELF: this one talks to the framebuffer and evdev directly.
 */
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>
#include <unistd.h>

#include "nova.h"

static int ptr_x = 200, ptr_y = 200;
#define REDRAW(call) do { nova_cursor_reset(); call; nova_cursor_draw(&fb, ptr_x, ptr_y); } while (0)

enum { VIEW_LIST, VIEW_ABOUT, VIEW_DISPLAY, VIEW_APPS };

static void draw_list(NovaFB *fb)
{
	static const char *titles[] = {"关于设备", "显示", "已安装应用", "语言", "关机"};
	static const char *subs[] = {
		"型号、内核与内存",
		"分辨率与像素格式",
		"/apps 中的应用",
		"中文 / English",
		"关闭计算机",
	};
	int y = 170;

	nova_app_header(fb, "设置");
	for (int i = 0; i < 5; i++) {
		uint32_t bg = (i == 4) ? 0x3a1620 : 0x1b2030;
		nova_round_rect(fb, 60, y, fb->w - 120, 88, 18, bg);
		nova_text(fb, 92, y + 20, titles[i], i == 4 ? 0xff8a8a : NOVA_WHITE, 2);
		nova_text(fb, 92, y + 52, subs[i], NOVA_DIM, 1);
		nova_text(fb, fb->w - 110, y + 30, ">", NOVA_DIM, 3);
		y += 104;
	}
}

static void read_first_line(const char *path, char *buf, size_t n)
{
	FILE *f = fopen(path, "r");

	buf[0] = '\0';
	if (!f)
		return;
	if (!fgets(buf, (int)n, f))
		buf[0] = '\0';
	fclose(f);
	buf[strcspn(buf, "\n")] = '\0';
}

static void draw_about(NovaFB *fb)
{
	struct utsname u;
	char line[128];
	int y = 180;

	uname(&u);
	nova_app_header(fb, "关于设备");
	nova_round_rect(fb, 60, y, fb->w - 120, 100, 18, 0x1e2438);
	nova_text(fb, 92, y + 18, "mubaiOS 0.2", NOVA_WHITE, 3);
	nova_text(fb, 92, y + 58, "基于 Linux 内核的桌面系统", NOVA_DIM, 2);

	y += 130;
	const char *labels[5] = {"内核", "架构", "帧缓冲", "内存", "根文件系统"};
	char values[5][128];

	snprintf(values[0], sizeof(values[0]), "%s %s", u.sysname, u.release);
	snprintf(values[1], sizeof(values[1]), "%s", u.machine);
	snprintf(values[2], sizeof(values[2]), "%dx%d, %d bpp", fb->w, fb->h, fb->bpp);
	read_first_line("/proc/meminfo", line, sizeof(line));
	snprintf(values[3], sizeof(values[3]), "%s", line);
	snprintf(values[4], sizeof(values[4]), "initramfs（内存）");

	for (int i = 0; i < 5; i++) {
		nova_text(fb, 70, y, labels[i], NOVA_DIM, 2);
		nova_text(fb, 420, y, values[i], NOVA_TEXT, 2);
		y += 46;
	}
}

static void draw_display(NovaFB *fb)
{
	nova_app_header(fb, "显示");
	nova_text(fb, 70, 180, "面板", NOVA_DIM, 2);
	char buf[128];
	snprintf(buf, sizeof(buf), "%d x %d 像素", fb->w, fb->h);
	nova_text(fb, 300, 180, buf, NOVA_TEXT, 2);

	nova_text(fb, 70, 240, "像素格式", NOVA_DIM, 2);
	snprintf(buf, sizeof(buf), "%d bpp, stride %d bytes", fb->bpp, fb->stride);
	nova_text(fb, 300, 240, buf, NOVA_TEXT, 2);

	nova_text(fb, 70, 300, "驱动", NOVA_DIM, 2);
	nova_text(fb, 300, 300, "bochs-drm (DRM fbdev emulation)", NOVA_TEXT, 2);

	nova_text(fb, 70, 380, "颜色测试", NOVA_DIM, 2);
	for (int i = 0; i < 8; i++)
		nova_round_rect(fb, 70 + i * 110, 420, 96, 96, 12,
				(uint32_t[]){0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71,
					     0x1abc9c, 0x3498db, 0x9b59b6, 0xecf0f1}[i]);
}

static void draw_apps(NovaFB *fb)
{
	nova_app_header(fb, "已安装应用");
	FILE *p = popen("ls /apps 2>/dev/null", "r");
	char line[128];
	int y = 180;

	if (!p)
		return;
	while (fgets(line, sizeof(line), p) && y < fb->h - 80) {
		line[strcspn(line, "\n")] = '\0';
		nova_round_rect(fb, 60, y, fb->w - 120, 64, 14, 0x1b2030);
		nova_text(fb, 90, y + 16, line, NOVA_TEXT, 2);
		y += 76;
	}
	pclose(p);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int view = VIEW_LIST;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	if (view == VIEW_LIST)
		REDRAW(draw_list(&fb));

	for (;;) {
		if (nova_poll(&in, &ev, 400) == 0)
			continue;
		ptr_x = ev.x;
		ptr_y = ev.y;
		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;

		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y)) {
				if (view == VIEW_LIST)
					return 0;
				view = VIEW_LIST;
				REDRAW(draw_list(&fb));
				continue;
			}
			if (view == VIEW_LIST) {
				int row = (ev.y - 170) / 104;
				if (ev.x < 60 || ev.x > fb.w - 60 || ev.y < 170 || row > 4)
					continue;
				if (row == 0) {
					view = VIEW_ABOUT;
					REDRAW(draw_about(&fb));
				} else if (row == 1) {
					view = VIEW_DISPLAY;
					REDRAW(draw_display(&fb));
				} else if (row == 2) {
					view = VIEW_APPS;
					REDRAW(draw_apps(&fb));
				} else if (row == 3) {
					FILE *cfg = fopen("/data/settings.conf", "w");
					if (cfg) {
						fprintf(cfg, "lang=%s\n", nova_lang() ? "zh" : "en");
						fclose(cfg);
					}
					nova_lang_reload();
					REDRAW(draw_list(&fb));
				} else {
					nova_fill(&fb, 0, 0, fb.w, fb.h, 0x000000);
					nova_text_center(&fb, fb.w / 2, fb.h / 2, "正在关机…",
							 NOVA_WHITE, 3);
					sync();
					sleep(1);
					kill(1, SIGTERM);
					return 0;
				}
			}
		}
	}
}
