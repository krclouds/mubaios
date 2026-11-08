/*
 * App Store -- mubaiOS's software catalogue.
 *
 * The catalogue ships inside the image under /store/apps.  "Install" copies an
 * app directory into /apps, where the launcher picks it up the next time it
 * scans; "uninstall" removes it again.  No network, no package manager daemon:
 * just files, which is enough for a system that boots from an initramfs.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include "nova.h"

struct item {
	const char *id;
	const char *name;
	const char *desc;
	const char *icon;
	uint32_t color;
};

static const struct item catalog[] = {
	{"clock", "时钟", "大字号时钟与日期", "钟", 0x2980b9},
	{"calc", "计算器", "加减乘除四则运算", "算", 0x16a085},
	{"snake", "贪吃蛇", "方向键控制的经典小游戏", "蛇", 0xc0392b},
	{"calendar", "日历", "月历", "历", 0xe67e22},
	{"weather", "天气", "五日预报", "天", 0x3498db},
	{"gallery", "相册", "程序化画作", "相", 0x8e44ad},
	{"music", "钢琴", "八键琴演示", "乐", 0xe84393},
	{"notes", "便签", "纯文本记事", "签", 0xf1c40f},
	{"minesweeper", "扫雷", "10×10 扫雷", "雷", 0x7f8c8d},
	{"game2048", "2048", "合并数字", "数", 0x16a085},
	{"stopwatch", "秒表", "计时工具", "秒", 0xd35400},
	{"sysmon", "系统监视", "负载与内存", "监", 0x2c3e50},
	{"compass", "指南针", "拖动旋转", "针", 0xc0392b},
	{"about", "关于", "系统信息", "关", 0x95a5a6},
};
#define ITEM_N (int)(sizeof(catalog) / sizeof(catalog[0]))

static int ptr_x = 400, ptr_y = 300;

static int installed(const char *id)
{
	char path[128];

	snprintf(path, sizeof(path), "/apps/%s/manifest", id);
	return access(path, R_OK) == 0;
}

static int count_installed(void)
{
	int n = 0;

	for (int i = 0; i < ITEM_N; i++)
		if (installed(catalog[i].id))
			n++;
	return n;
}

static int copy_file(const char *src, const char *dst, mode_t mode)
{
	char buf[65536];
	int in = open(src, O_RDONLY);
	int out;
	ssize_t n;

	if (in < 0)
		return -1;
	out = open(dst, O_WRONLY | O_CREAT | O_TRUNC, mode);
	if (out < 0) {
		close(in);
		return -1;
	}
	while ((n = read(in, buf, sizeof(buf))) > 0)
		if (write(out, buf, (size_t)n) != n) {
			close(in);
			close(out);
			return -1;
		}
	close(in);
	close(out);
	return 0;
}

static int do_install(const char *id)
{
	char dir[128], src[192], dst[192];

	snprintf(dir, sizeof(dir), "/apps/%s", id);
	mkdir(dir, 0755);
	snprintf(src, sizeof(src), "/store/apps/%s/%s", id, id);
	snprintf(dst, sizeof(dst), "/apps/%s/%s", id, id);
	if (copy_file(src, dst, 0755) != 0)
		return -1;
	snprintf(src, sizeof(src), "/store/apps/%s/manifest", id);
	snprintf(dst, sizeof(dst), "/apps/%s/manifest", id);
	return copy_file(src, dst, 0644);
}

static void do_remove(const char *id)
{
	char path[192];

	snprintf(path, sizeof(path), "/apps/%s/%s", id, id);
	unlink(path);
	snprintf(path, sizeof(path), "/apps/%s/manifest", id);
	unlink(path);
	snprintf(path, sizeof(path), "/apps/%s", id);
	rmdir(path);
}

static void do_open(const char *id)
{
	char path[128];
	pid_t pid;

	snprintf(path, sizeof(path), "/apps/%s/%s", id, id);
	pid = fork();
	if (pid == 0) {
		execl(path, path, (char *)NULL);
		_exit(127);
	}
	if (pid > 0)
		waitpid(pid, NULL, 0);
}

static void card_button(NovaFB *fb, int x, int y, int w, const char *label,
			uint32_t bg, uint32_t fg)
{
	nova_round_rect(fb, x, y, w, 40, 12, bg);
	nova_text_center(fb, x + w / 2, y + 8, label, fg, 1);
}

static void layout(NovaFB *fb, int *cw, int *ch, int *gap, int *x0, int *y0, int *cols)
{
	*gap = 16;
	*cols = 3;
	*cw = (fb->w - 120 - 2 * (*gap)) / 3;
	*ch = 104;
	*x0 = 60;
	*y0 = 190;
}

static void draw(NovaFB *fb)
{
	char line[64];
	int cw, ch, gap, x0, y0, cols;

	layout(fb, &cw, &ch, &gap, &x0, &y0, &cols);
	nova_cursor_reset();
	nova_app_header(fb, "应用商店");
	snprintf(line, sizeof(line), L("共 %d 个应用，已安装 %d 个", "%d apps, %d installed"), ITEM_N, count_installed());
	nova_text(fb, 60, 140, line, NOVA_DIM, 1);

	for (int i = 0; i < ITEM_N; i++) {
		const struct item *it = &catalog[i];
		int col = i % cols, row = i / cols;
		int x = x0 + col * (cw + gap), y = y0 + row * (ch + gap);
		int inst = installed(it->id);

		nova_round_rect(fb, x, y, cw, ch, 16, 0x1e2438);
		nova_round_rect_gradient(fb, x + 14, y + 20, 64, 64, 16, it->color,
					 (it->color & 0xfefefe) >> 1);
		nova_text(fb, x + 30, y + 38, it->icon, NOVA_WHITE, 2);
		nova_text(fb, x + 92, y + 18, it->name, NOVA_WHITE,
			  nova_text_width(it->name, 2) > cw - 210 ? 1 : 2);
		nova_text(fb, x + 92, y + 56, it->desc, NOVA_DIM, 1);

		if (inst) {
			card_button(fb, x + cw - 152, y + 32, 84, "打开", 0x2ecc71, 0x08130c);
			card_button(fb, x + cw - 60, y + 32, 44, "卸", 0x3a1620, 0xff8a8a);
		} else {
			card_button(fb, x + cw - 108, y + 32, 92, "安装", NOVA_ACCENT, NOVA_WHITE);
		}
	}
	nova_cursor_draw(fb, ptr_x, ptr_y);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int cw, ch, gap, x0, y0, cols;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	layout(&fb, &cw, &ch, &gap, &x0, &y0, &cols);
	draw(&fb);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		ptr_x = ev.x;
		ptr_y = ev.y;

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

		for (int i = 0; i < ITEM_N; i++) {
			const struct item *it = &catalog[i];
			int col = i % cols, row = i / cols;
			int x = x0 + col * (cw + gap), y = y0 + row * (ch + gap);

			if (installed(it->id)) {
				if (nova_hit(ev.x, ev.y, x + cw - 152, y + 32, 84, 40))
					do_open(it->id);
				else if (nova_hit(ev.x, ev.y, x + cw - 60, y + 32, 44, 40))
					do_remove(it->id);
			} else if (nova_hit(ev.x, ev.y, x + cw - 108, y + 32, 92, 40)) {
				do_install(it->id);
			}
		}
		draw(&fb);
	}
}
