/*
 * 开源许可 -- the open-source statement, shipped inside the system itself.
 *
 * Page 1: what is MIT, what is third-party, what is not included, how to verify.
 * Page 2: the verbatim MIT license text from /system/share/LICENSE.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>

#include "nova.h"

#define BODY_Y 300

static const char *left_lines[] = {
	"H 本项目（MIT）",
	"B src/       24 个 .c，5 786 行",
	"B            用户态全部在这里",
	"B build.py   内核、编译、字库、initramfs",
	"B build_iso.py  BIOS 可引导 ISO",
	"B rootfs/    启动与安装脚本",
	"B tools/     字库、拼音、QA、发布",
	"",
	"H 不包含",
	"B 专有 SDK、反编译代码、商业游戏资源",
	NULL,
};

static const char *right_lines[] = {
	"H 第三方（开源，未修改）",
	"B Linux 6.1 内核与模块      GPL-2.0",
	"B BusyBox                   GPL-2.0",
	"B glibc 运行时              LGPL-2.1",
	"B libgcc_s.so.1             GPL+例外",
	"B Noto Sans CJK SC          OFL-1.1",
	"B DejaVu Sans Mono          Bitstream Vera",
	"B Unihan kMandarin          Unicode License",
	"",
	"H 源码与许可",
	"B github.com/krclouds/mubaios",
	"B /system/share/LICENSE",
	"B /system/share/OPEN_SOURCE.md",
	"B /system/share/THIRD_PARTY.md",
	NULL,
};

#define MAX_LICENSE_LINES 64
static char license_text[MAX_LICENSE_LINES][96];
static int license_n;

static void load_license(void)
{
	FILE *f = fopen("/system/share/LICENSE", "r");
	char buf[256];

	license_n = 0;
	if (!f)
		return;
	while (license_n < MAX_LICENSE_LINES && fgets(buf, sizeof(buf), f)) {
		buf[strcspn(buf, "\r\n")] = 0;
		snprintf(license_text[license_n], sizeof(license_text[0]), "%s", buf);
		license_n++;
	}
	fclose(f);
}

static void draw_lines(NovaFB *fb, const char **lines, int x, int y)
{
	for (int i = 0; lines[i]; i++) {
		if (lines[i][0] == 0) {
			y += 8;
			continue;
		}
		if (lines[i][0] == 'H') {
			nova_text(fb, x, y, lines[i] + 1, 0x8b5cff, 2);
			y += 40;
		} else {
			nova_text(fb, x, y, lines[i] + 1, NOVA_TEXT, 1);
			y += 26;
		}
	}
}

static void draw_page1(NovaFB *fb)
{
	nova_fill(fb, 0, 0, fb->w, fb->h, 0x0b0d14);
	nova_app_header(fb, "开源许可");

	nova_round_rect(fb, 60, 146, fb->w - 120, 118, 18, 0x14263a);
	nova_text(fb, 92, 164, "mubaiOS 0.1", NOVA_WHITE, 3);
	int tag_x = 92 + nova_text_width("mubaiOS 0.1", 3) + 28;
	nova_round_rect(fb, tag_x, 172, 176, 40, 12, 0x0e7490);
	nova_text(fb, tag_x + 18, 182, "MIT License", 0xffffff, 2);
	nova_text(fb, 92, 222, "用户态全部开源，从源码可重建同一个镜像", NOVA_DIM, 1);

	draw_lines(fb, left_lines, 80, BODY_Y);
	draw_lines(fb, right_lines, 660, BODY_Y);

	nova_text(fb, 80, fb->h - 64, "Tab 或右下角按钮：查看 MIT 原文 · Esc 返回", 0x4a5068, 1);
	nova_round_rect(fb, fb->w - 280, fb->h - 78, 200, 52, 14, 0x6c5ce7);
	nova_text(fb, fb->w - 246, fb->h - 66, "查看原文", NOVA_WHITE, 2);
}

static int page2_scroll;

static void draw_page2(NovaFB *fb)
{
	int y = 160;
	int rows = (fb->h - 160 - 100) / 26;

	nova_fill(fb, 0, 0, fb->w, fb->h, 0x0b0d14);
	nova_app_header(fb, "MIT 许可证原文");

	if (license_n == 0) {
		nova_text(fb, 80, y + 30, "找不到 /system/share/LICENSE", 0xf87171, 2);
	} else {
		for (int i = 0; i < rows; i++) {
			int idx = page2_scroll + i;
			if (idx >= license_n)
				break;
			nova_text(fb, 80, y, license_text[idx], NOVA_TEXT, 1);
			y += 26;
		}
	}

	nova_text(fb, 80, fb->h - 64, "滚轮/方向键翻页 · Tab 回到概览 · Esc 返回", 0x4a5068, 1);
	nova_round_rect(fb, fb->w - 240, fb->h - 78, 160, 52, 14, 0x1e2438);
	nova_text(fb, fb->w - 210, fb->h - 66, "概览", NOVA_WHITE, 2);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int page = 1;
	int px = 640, py = 400;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	load_license();
	draw_page1(&fb);
	nova_flush(&fb);

	for (;;) {
		if (nova_poll(&in, &ev, 300) == 0)
			continue;
		px = ev.x;
		py = ev.y;

		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && (ev.key == 1 || ev.key == 18))
			return 0;
		if (ev.type == NOVA_KEY && ev.key == 15) {	/* Tab */
			page = (page == 1) ? 2 : 1;
			page2_scroll = 0;
		}
		if (ev.type == NOVA_KEY && ev.key == 108 && page == 2)	/* Down */
			if (page2_scroll + 4 < license_n)
				page2_scroll += 4;
		if (ev.type == NOVA_KEY && ev.key == 103 && page == 2)	/* Up */
			if (page2_scroll >= 4)
				page2_scroll -= 4;

		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y))
				return 0;
			if (ev.y > fb.h - 90 && ev.x > fb.w - 300)
				page = (page == 1) ? 2 : 1;
		}
		if (ev.type == NOVA_WHEEL && page == 2) {
			if (ev.key > 0 && page2_scroll + 2 < license_n)
				page2_scroll += 2;
			if (ev.key < 0 && page2_scroll >= 2)
				page2_scroll -= 2;
		}

		nova_cursor_reset();
		if (page == 1)
			draw_page1(&fb);
		else
			draw_page2(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
