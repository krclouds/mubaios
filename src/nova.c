/*
 * nova.c -- mubaiOS application SDK implementation.
 *
 * Framebuffer access, drawing primitives, an 8x16 bitmap font and evdev input.
 * Deliberately dependency-free: musl + the kernel, nothing else.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <linux/input.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"
#include "font8x16.h"
#include "font_cjk.h"

static int fb_dirty;
static int dirty_x0, dirty_y0, dirty_x1, dirty_y1;
static int dirty_valid;

static inline void dirty_add(int x, int y)
{
	if (!dirty_valid) {
		dirty_x0 = dirty_x1 = x;
		dirty_y0 = dirty_y1 = y;
		dirty_valid = 1;
		return;
	}
	if (x < dirty_x0) dirty_x0 = x;
	if (x > dirty_x1) dirty_x1 = x;
	if (y < dirty_y0) dirty_y0 = y;
	if (y > dirty_y1) dirty_y1 = y;
}

static inline void dirty_clear(void)
{
	dirty_valid = 0;
}


struct tr_pair { const char *zh, *en; };

static const struct tr_pair tr_table[] = {
	{"设置", "Settings"}, {"文件", "Files"}, {"画板", "Paint"}, {"终端", "Terminal"},
	{"应用商店", "App Store"}, {"时钟", "Clock"}, {"计算器", "Calculator"},
	{"天气", "Weather"}, {"相册", "Gallery"}, {"钢琴", "Piano"}, {"便签", "Notes"},
	{"扫雷", "Minesweeper"}, {"秒表", "Stopwatch"}, {"系统监视", "System Monitor"},
	{"指南针", "Compass"}, {"关于", "About"}, {"关于设备", "About device"},
	{"型号、内核与内存", "Model, kernel and memory"}, {"显示", "Display"},
	{"分辨率与像素格式", "Resolution and pixel format"}, {"已安装应用", "Installed apps"},
	{"/apps 中的应用", "Apps in /apps"}, {"关机", "Power off"},
	{"关闭计算机", "Shut the machine down"}, {"语言", "Language"},
	{"面板", "Panel"}, {"像素", "pixels"}, {"像素格式", "Pixel format"},
	{"驱动", "Driver"}, {"颜色测试", "Colour test"}, {"正在关机…", "Powering off..."},
	{"内核", "Kernel"}, {"架构", "Architecture"}, {"帧缓冲", "Framebuffer"},
	{"内存", "Memory"}, {"根文件系统", "Root filesystem"},
	{"initramfs（内存）", "initramfs (in memory)"},
	{"基于 Linux 内核的桌面系统", "A desktop system on the Linux kernel"},
	{"自研用户态 + Linux 内核的类 Android 系统", "Custom user space on the Linux kernel"},
	{"基于 Linux 内核，用户态全部自研", "Linux kernel, user space written from scratch"},
	{"5 个预装 + 应用商店", "5 preinstalled + App Store"},
	{"欢迎回来", "Welcome back"}, {"没有最近的应用", "No recent apps"},
	{"查看器", "Viewer"}, {"空目录", "empty directory"},
	{"(二进制或空文件)", "(binary or empty file)"},
	{"输入命令，回车执行", "Type a command, Enter to run"},
	{"键盘", "Keyboard"}, {"空格", "Space"}, {"退格", "Backspace"},
	{"回车", "Enter"}, {"小写", "Shift"}, {"大写", "SHIFT"},
	{"mubaiOS 0.2 终端", "mubaiOS 0.2 terminal"},
	{"命令经由 /bin/sh (BusyBox) 执行", "Commands run through /bin/sh (BusyBox)"},
	{"试试：uname -a、ls /apps、free", "Try: uname -a, ls /apps, free"},
	{"没有实体键盘时，点右上角「键盘」用鼠标输入", "No hardware keyboard? Tap the keyboard button"},
	{"用手指或鼠标绘制 · 可撤销", "Draw with a finger or the mouse"},
	{"撤销", "Undo"}, {"清空", "Clear"}, {"输入算式", "Enter an expression"},
	{"游戏结束", "Game over"}, {"点击重新开始", "Tap to restart"},
	{"背包 (E)", "Inventory (E)"}, {"创造模式物品栏", "Creative inventory"},
	{"E 关闭", "E to close"}, {"该分类暂无物品", "No items in this category"},
	{"mubaiOS 的方块世界还没有这一栏的内容", "This tab has no blocks yet"},
	{"全部", "All"}, {"刷怪蛋", "Spawn eggs"}, {"武器与战斗", "Weapons"},
	{"工具与采集", "Tools"}, {"护甲与装备", "Armour"}, {"食物与农业", "Food"},
	{"药水与炼药", "Potions"}, {"运输与容器", "Transport"}, {"书籍与导航", "Books"},
	{"装饰与纹样", "Decoration"}, {"音乐与收藏", "Music"}, {"材料与矿物", "Materials"},
	{"放置与实体", "Blocks"}, {"功能与特殊物品", "Special"},
	{"草方块", "Grass"}, {"泥土", "Dirt"}, {"石头", "Stone"}, {"圆石", "Cobblestone"},
	{"沙子", "Sand"}, {"沙砾", "Gravel"}, {"原木", "Log"}, {"木板", "Planks"},
	{"树叶", "Leaves"}, {"水", "Water"}, {"冰", "Ice"}, {"雪", "Snow"},
	{"玻璃", "Glass"}, {"砖块", "Bricks"}, {"煤炭矿石", "Coal ore"},
	{"铁矿石", "Iron ore"}, {"金矿石", "Gold ore"}, {"钻石矿石", "Diamond ore"},
	{"羊毛", "Wool"}, {"黑曜石", "Obsidian"}, {"熔岩", "Lava"},
	{"北京", "Beijing"}, {"演示数据 · 无网络", "Demo data · offline"},
	{"刷新", "Refresh"}, {"今天", "Today"}, {"明天", "Tomorrow"},
	{"第三天", "Day 3"}, {"第四天", "Day 4"}, {"第五天", "Day 5"},
	{"晴", "Sunny"}, {"多云", "Cloudy"}, {"小雨", "Light rain"}, {"阴", "Overcast"},
	{"日落", "Sunset"}, {"群山", "Mountains"}, {"海面", "Sea"}, {"城市", "City"},
	{"圆", "Circles"}, {"森林", "Forest"},
	{"点击琴键 · 本机暂无音频驱动，仅演示交互", "Tap the keys · no audio driver yet"},
	{"键盘输入 · Esc 保存并退出", "Type with the keyboard · Esc saves and exits"},
	{"点这里……其实请直接用键盘输入", "Empty note. Just start typing."},
	{"切换标记", "Toggle flag"}, {"重来", "Restart"},
	{"扫雷成功", "Cleared!"}, {"踩到地雷", "Boom!"},
	{"点「重来」再开一局", "Tap Restart to play again"}, {"旗", "F"},
	{"点「重来」继续", "Tap Restart to continue"}, {"方向键移动", "Arrow keys to move"},
	{"开始", "Start"}, {"暂停", "Pause"}, {"重置", "Reset"},
	{"负载 (1/5/15 分钟)", "Load (1/5/15 min)"}, {"CPU 核心", "CPU cores"},
	{"北", "N"}, {"东", "E"}, {"南", "S"}, {"西", "W"},
	{"左右拖动旋转表盘", "Drag left/right to rotate"},
	{"安装", "Install"}, {"打开", "Open"}, {"卸", "Del"},
	{"大字号时钟与日期", "Big clock and date"},
	{"加减乘除四则运算", "Basic arithmetic"},
	{"方向键控制的经典小游戏", "Classic snake game"},
	{"方块沙盒", "Block sandbox"},
	{"月历", "Month view"},
	{"五日预报", "5-day forecast"},
	{"程序化画作", "Procedural art"},
	{"八键琴演示", "Eight-key piano"},
	{"纯文本记事", "Plain text notes"},
	{"10×10 扫雷", "10x10 minesweeper"},
	{"合并数字", "Merge the numbers"},
	{"计时工具", "Stopwatch"},
	{"负载与内存", "Load and memory"},
	{"拖动旋转", "Drag to rotate"},
	{"系统信息", "System info"},
	{"设", "S"}, {"文", "F"}, {"画", "P"}, {"终", "T"}, {"店", "M"},
	{"钟", "C"}, {"算", "="}, {"蛇", "S"}, {"界", "W"}, {"历", "D"},
	{"天", "W"}, {"相", "G"}, {"乐", "M"}, {"签", "N"}, {"雷", "X"},
	{"数", "2"}, {"秒", "T"}, {"监", "M"}, {"针", "C"}, {"关", "i"},
};

static int lang_cache = -1;

void nova_lang_reload(void)
{
	lang_cache = -1;
}

int nova_lang(void)
{
	if (lang_cache < 0) {
		FILE *f = fopen("/data/settings.conf", "r");
		char line[64];

		lang_cache = 0;
		while (f && fgets(line, sizeof(line), f))
			if (strncmp(line, "lang=en", 7) == 0)
				lang_cache = 1;
		if (f)
			fclose(f);
	}
	return lang_cache;
}

const char *nova_tr(const char *s)
{
	if (!nova_lang() || !s)
		return s;
	for (size_t i = 0; i < sizeof(tr_table) / sizeof(tr_table[0]); i++)
		if (strcmp(tr_table[i].zh, s) == 0)
			return tr_table[i].en;
	return s;
}


static uint32_t lerp_color(uint32_t a, uint32_t b, int t, int total);
static int g_screen_w = 1280, g_screen_h = 800;

/* ------------------------------------------------------------------ */
/* framebuffer                                                         */
/* ------------------------------------------------------------------ */

int nova_fb_open(NovaFB *fb)
{
	struct fb_var_screeninfo vi;
	struct fb_fix_screeninfo fi;

	memset(fb, 0, sizeof(*fb));
	fb->fd = open("/dev/fb0", O_RDWR | O_CLOEXEC);
	if (fb->fd < 0)
		return -1;
	if (ioctl(fb->fd, FBIOGET_VSCREENINFO, &vi) < 0 ||
	    ioctl(fb->fd, FBIOGET_FSCREENINFO, &fi) < 0) {
		close(fb->fd);
		return -1;
	}
	fb->w = vi.xres;
	fb->h = vi.yres;
	fb->bpp = vi.bits_per_pixel;
	fb->stride = fi.line_length;
	fb->len = (size_t)fb->stride * fb->h;
	fb->buf = calloc((size_t)fb->w * (size_t)fb->h, sizeof(uint32_t));
	if (!fb->buf) {
		close(fb->fd);
		return -1;
	}
	fb->mem = mmap(NULL, fb->len, PROT_READ | PROT_WRITE, MAP_SHARED, fb->fd, 0);
	if (fb->mem == MAP_FAILED) {
		close(fb->fd);
		return -1;
	}
	return 0;
}

void nova_fb_close(NovaFB *fb)
{
	if (fb->mem && fb->mem != MAP_FAILED)
		munmap(fb->mem, fb->len);
	if (fb->fd >= 0)
		close(fb->fd);
	fb->mem = NULL;
	fb->fd = -1;
}

static inline void put_px(NovaFB *fb, int x, int y, uint32_t c)
{
	if (x < 0 || y < 0 || x >= fb->w || y >= fb->h)
		return;
	if (fb->bpp == 32) {
		fb->buf[(size_t)y * fb->w + x] = c;
		fb_dirty = 1;
		dirty_add(x, y);
	} else if (fb->bpp == 16) {
		uint16_t v = (uint16_t)(((c >> 19) & 0x1f) << 11 |
					((c >> 10) & 0x3f) << 5 |
					((c >> 3) & 0x1f));
		*(uint16_t *)(fb->mem + (size_t)y * fb->stride + (size_t)x * 2) = v;
	}
}

void nova_pixel(NovaFB *fb, int x, int y, uint32_t color)
{
	put_px(fb, x, y, color);
}

uint32_t nova_get(NovaFB *fb, int x, int y)
{
	if (x < 0 || y < 0 || x >= fb->w || y >= fb->h)
		return 0;
	if (fb->bpp == 32)
		return fb->buf[(size_t)y * fb->w + x];
	if (fb->bpp == 16) {
		uint16_t v = *(uint16_t *)(fb->mem + (size_t)y * fb->stride + (size_t)x * 2);
		uint32_t r = (v >> 11) & 0x1f, g = (v >> 5) & 0x3f, b = v & 0x1f;
		return (r << 19) | (g << 10) | b;
	}
	return 0;
}

void nova_fill(NovaFB *fb, int x, int y, int w, int h, uint32_t color)
{
	int x0 = x < 0 ? 0 : x;
	int y0 = y < 0 ? 0 : y;
	int x1 = x + w > fb->w ? fb->w : x + w;
	int y1 = y + h > fb->h ? fb->h : y + h;

	if (x1 <= x0 || y1 <= y0)
		return;

	if (fb->bpp == 32) {
		fb_dirty = 1;
		for (int yy = y0; yy < y1; yy++) {
			uint32_t *row = fb->buf + (size_t)yy * fb->w;
			for (int xx = x0; xx < x1; xx++)
				row[xx] = color;
		}
	} else {
		for (int yy = y0; yy < y1; yy++)
			for (int xx = x0; xx < x1; xx++)
				put_px(fb, xx, yy, color);
	}
}


int nova_dirty(void)
{
	return fb_dirty;
}

void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h)
{
	int x0 = x < 0 ? 0 : x, y0 = y < 0 ? 0 : y;
	int x1 = x + w > fb->w ? fb->w : x + w;
	int y1 = y + h > fb->h ? fb->h : y + h;

	if (!fb->buf || fb->bpp != 32 || x1 <= x0 || y1 <= y0)
		return;
	for (int yy = y0; yy < y1; yy++)
		memcpy(fb->mem + (size_t)yy * fb->stride + (size_t)x0 * 4,
		       fb->buf + (size_t)yy * fb->w + x0, (size_t)(x1 - x0) * 4);
	if (x0 <= dirty_x0 && y0 <= dirty_y0 && x1 > dirty_x1 && y1 > dirty_y1)
		dirty_clear();
}

void nova_mark_clean(void)
{
	fb_dirty = 0;
}

void nova_flush(NovaFB *fb)
{
	if (!fb->buf || fb->bpp != 32)
		return;
	if ((size_t)fb->stride == (size_t)fb->w * 4) {
		memcpy(fb->mem, fb->buf, (size_t)fb->w * fb->h * 4);
	} else {
		for (int y = 0; y < fb->h; y++)
			memcpy(fb->mem + (size_t)y * fb->stride,
			       fb->buf + (size_t)y * fb->w, (size_t)fb->w * 4);
	}
	fb_dirty = 0;
	dirty_clear();
}

static int isqrt_i(int v)
{
	int r = 0;

	if (v <= 0)
		return 0;
	while ((r + 1) * (r + 1) <= v)
		r++;
	return r;
}

void nova_round_rect(NovaFB *fb, int x, int y, int w, int h, int r, uint32_t color)
{
	if (r <= 0) {
		nova_fill(fb, x, y, w, h, color);
		return;
	}
	if (r * 2 > w)
		r = w / 2;
	if (r * 2 > h)
		r = h / 2;
	for (int dy = 0; dy < h; dy++) {
		int inset = 0;
		if (dy < r)
			inset = r - isqrt_i(r * r - (r - dy) * (r - dy));
		else if (dy >= h - r)
			inset = r - isqrt_i(r * r - (dy - (h - r - 1)) * (dy - (h - r - 1)));
		nova_fill(fb, x + inset, y + dy, w - 2 * inset, 1, color);
	}
}

void nova_round_rect_gradient(NovaFB *fb, int x, int y, int w, int h, int r,
			      uint32_t top, uint32_t bottom)
{
	if (r * 2 > w)
		r = w / 2;
	if (r * 2 > h)
		r = h / 2;
	for (int dy = 0; dy < h; dy++) {
		int inset = 0;
		if (dy < r)
			inset = r - isqrt_i(r * r - (r - dy) * (r - dy));
		else if (dy >= h - r)
			inset = r - isqrt_i(r * r - (dy - (h - r - 1)) * (dy - (h - r - 1)));
		nova_fill(fb, x + inset, y + dy, w - 2 * inset, 1,
			  lerp_color(top, bottom, dy, h - 1));
	}
}

void nova_round_outline(NovaFB *fb, int x, int y, int w, int h, int r,
			int thickness, uint32_t color)
{
	for (int t = 0; t < thickness; t++)
		nova_round_rect(fb, x + t, y + t, w - 2 * t, h - 2 * t, r - t, color);
	nova_round_rect(fb, x + thickness, y + thickness, w - 2 * thickness,
			h - 2 * thickness, r - thickness, 0x101018);
}

void nova_line(NovaFB *fb, int x0, int y0, int x1, int y1, uint32_t color)
{
	int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
	int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
	int err = dx + dy;

	for (;;) {
		put_px(fb, x0, y0, color);
		if (x0 == x1 && y0 == y1)
			break;
		int e2 = 2 * err;
		if (e2 >= dy) {
			err += dy;
			x0 += sx;
		}
		if (e2 <= dx) {
			err += dx;
			y0 += sy;
		}
	}
}

void nova_circle(NovaFB *fb, int cx, int cy, int r, uint32_t color)
{
	for (int dy = -r; dy <= r; dy++) {
		int dx = isqrt_i(r * r - dy * dy);
		nova_fill(fb, cx - dx, cy + dy, 2 * dx + 1, 1, color);
	}
}

static uint32_t lerp_color(uint32_t a, uint32_t b, int t, int total)
{
	int ar = (a >> 16) & 0xff, ag = (a >> 8) & 0xff, ab = a & 0xff;
	int br = (b >> 16) & 0xff, bg = (b >> 8) & 0xff, bb = b & 0xff;

	if (total <= 0)
		total = 1;
	int rr = ar + (br - ar) * t / total;
	int rg = ag + (bg - ag) * t / total;
	int rb = ab + (bb - ab) * t / total;
	return (uint32_t)((rr << 16) | (rg << 8) | rb);
}

void nova_gradient(NovaFB *fb, int x, int y, int w, int h, uint32_t top, uint32_t bottom)
{
	for (int dy = 0; dy < h; dy++)
		nova_fill(fb, x, y + dy, w, 1, lerp_color(top, bottom, dy, h - 1));
}

/* ------------------------------------------------------------------ */
/* text                                                                */
/* ------------------------------------------------------------------ */

/* ---------------------------------------------------------------- */
/* font file: /system/share/font.bin (rasterised from DejaVuSansMono    */
/* and NotoSansCJKsc at build time, 8-bit alpha)                       */
/* ---------------------------------------------------------------- */

struct fontfile {
	unsigned char *data;
	int ascii_first, ascii_count, aw, ah;
	int cjk_count, cw, ch;
	const unsigned char *ascii_tab;
	const unsigned char *cjk_tab;
	int loaded, ok;
};

static struct fontfile g_font;

static unsigned int rd32(const unsigned char *p)
{
	return (unsigned int)p[0] | ((unsigned int)p[1] << 8) |
	       ((unsigned int)p[2] << 16) | ((unsigned int)p[3] << 24);
}

static void font_init(void)
{
	unsigned char *buf;
	unsigned int ver, ac, aw, ah, cc, cw, ch;
	long size;
	int fd, got;

	if (g_font.loaded)
		return;
	g_font.loaded = 1;
	fd = open("/system/share/font.bin", O_RDONLY);
	if (fd < 0)
		return;
	size = (long)lseek(fd, 0, SEEK_END);
	lseek(fd, 0, SEEK_SET);
	if (size < 44 || size > 8 * 1024 * 1024) {
		close(fd);
		return;
	}
	buf = malloc((size_t)size);
	if (!buf) {
		close(fd);
		return;
	}
	got = (int)read(fd, buf, (size_t)size);
	close(fd);
	if (got != (int)size) {
		free(buf);
		return;
	}
	if (memcmp(buf, "NOVAFONT", 8) != 0) {
		free(buf);
		return;
	}
	ver = rd32(buf + 8);
	ac = rd32(buf + 16);
	aw = rd32(buf + 20);
	ah = rd32(buf + 24);
	cc = rd32(buf + 28);
	cw = rd32(buf + 32);
	ch = rd32(buf + 36);
	if (ver != 1 || aw != 8 || ah != 16 || cw != 16 || ch != 16) {
		free(buf);
		return;
	}
	g_font.data = buf;
	g_font.ascii_first = (int)rd32(buf + 12);
	g_font.ascii_count = (int)ac;
	g_font.aw = (int)aw;
	g_font.ah = (int)ah;
	g_font.cjk_count = (int)cc;
	g_font.cw = (int)cw;
	g_font.ch = (int)ch;
	g_font.ascii_tab = buf + 44;
	g_font.cjk_tab = g_font.ascii_tab + (size_t)ac * (4 + aw * ah);
	g_font.ok = 1;
}

static const unsigned char *font_ascii(int ch)
{
	int idx = ch - g_font.ascii_first;
	int stride = 4 + g_font.aw * g_font.ah;

	if (idx < 0 || idx >= g_font.ascii_count)
		return NULL;
	return g_font.ascii_tab + (size_t)idx * stride + 4;
}

static const unsigned char *font_cjk(unsigned int cp)
{
	int stride = 4 + g_font.cw * g_font.ch;
	int lo = 0, hi = g_font.cjk_count - 1;

	while (lo <= hi) {
		int mid = (lo + hi) / 2;
		const unsigned char *rec = g_font.cjk_tab + (size_t)mid * stride;
		unsigned int c = rd32(rec);
		if (c == cp)
			return rec + 4;
		if (c < cp)
			lo = mid + 1;
		else
			hi = mid - 1;
	}
	return NULL;
}

static void font_blit(NovaFB *fb, int x, int y, const unsigned char *a,
		      int w, int h, uint32_t color, int scale)
{
	for (int row = 0; row < h; row++)
		for (int col = 0; col < w; col++) {
			int alpha = a[row * w + col];

			if (!alpha)
				continue;
			for (int sy = 0; sy < scale; sy++)
				for (int sx = 0; sx < scale; sx++)
					nova_blend_px(fb, x + col * scale + sx,
						      y + row * scale + sy, color, alpha);
		}
}

static const unsigned short *cjk_lookup(unsigned int cp)
{
	int lo = 0, hi = cjk_glyph_count - 1;

	while (lo <= hi) {
		int mid = (lo + hi) / 2;
		if (cjk_glyphs[mid].cp == cp)
			return cjk_glyphs[mid].rows;
		if (cjk_glyphs[mid].cp < cp)
			lo = mid + 1;
		else
			hi = mid - 1;
	}
	return NULL;
}

static int utf8_next(const unsigned char **pp, unsigned int *cp)
{
	const unsigned char *p = *pp;

	if (*p < 0x80) {
		*cp = *p;
		*pp = p + 1;
		return 1;
	}
	if ((*p & 0xe0) == 0xc0 && p[1]) {
		*cp = ((unsigned)(p[0] & 0x1f) << 6) | (p[1] & 0x3f);
		*pp = p + 2;
		return 2;
	}
	if ((*p & 0xf0) == 0xe0 && p[1] && p[2]) {
		*cp = ((unsigned)(p[0] & 0x0f) << 12) | ((unsigned)(p[1] & 0x3f) << 6) | (p[2] & 0x3f);
		*pp = p + 3;
		return 3;
	}
	*cp = '?';
	*pp = p + 1;
	return 1;
}

static int char_width(unsigned int cp)
{
	return cp < 0x80 ? 8 : 16;
}

int nova_text_width(const char *s, int scale)
{
	const unsigned char *p;

	s = nova_tr(s);
	p = (const unsigned char *)s;
	unsigned int cp;
	int w = 0;

	while (*p) {
		utf8_next(&p, &cp);
		w += char_width(cp);
	}
	return w * scale;
}

void nova_text(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale)
{
	const unsigned char *p;

	s = nova_tr(s);
	p = (const unsigned char *)s;
	unsigned int cp;

	if (scale < 1)
		scale = 1;
	font_init();
	while (*p) {
		utf8_next(&p, &cp);
		if (cp < 0x80) {
			int ch = (int)cp;
			if (ch < 32 || ch > 126)
				ch = '?';
			if (g_font.ok) {
				const unsigned char *g = font_ascii(ch);

				if (!g) {
					x += g_font.aw * scale;
					continue;
				}
				font_blit(fb, x, y, g, g_font.aw, g_font.ah, color, scale);
				x += g_font.aw * scale;
				continue;
			}
			const unsigned char *glyph = font8x16[ch - 32];
			for (int row = 0; row < 16; row++)
				for (int col = 0; col < 8; col++)
					if (glyph[row] & (0x80 >> col))
						nova_fill(fb, x + col * scale, y + row * scale, scale, scale, color);
			x += 8 * scale;
		} else {
			const unsigned char *g;

			if (g_font.ok && (g = font_cjk(cp)) != NULL) {
				font_blit(fb, x, y, g, g_font.cw, g_font.ch, color, scale);
				x += g_font.cw * scale;
				continue;
			}
			const unsigned short *glyph = cjk_lookup(cp);
			if (!glyph) {
				x += 16 * scale;
				continue;
			}
			for (int row = 0; row < 16; row++)
				for (int col = 0; col < 16; col++)
					if (glyph[row] & (0x8000 >> col))
						nova_fill(fb, x + col * scale, y + row * scale, scale, scale, color);
			x += 16 * scale;
		}
	}
}

void nova_text_center(NovaFB *fb, int cx, int y, const char *s, uint32_t color, int scale)
{
	nova_text(fb, cx - nova_text_width(s, scale) / 2, y, s, color, scale);
}

/* ------------------------------------------------------------------ */
/* shared widgets                                                      */
/* ------------------------------------------------------------------ */

void nova_clock(char *buf, size_t n)
{
	time_t now = time(NULL);
	struct tm tm;

	localtime_r(&now, &tm);
	snprintf(buf, n, "%02d:%02d", tm.tm_hour, tm.tm_min);
}

void nova_status_bar(NovaFB *fb, const char *left, const char *right)
{
	static const char *const wd_zh[] = { "星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六" };
	char date[40], clock[16];
	time_t now = time(NULL);
	struct tm tm;
	int bx, dw;

	(void)left;
	localtime_r(&now, &tm);
	if (right && *right)
		snprintf(clock, sizeof(clock), "%s", right);
	else
		snprintf(clock, sizeof(clock), "%02d:%02d", tm.tm_hour, tm.tm_min);
	if (nova_lang() == 0)
		snprintf(date, sizeof(date), "%d月%d日 %s", tm.tm_mon + 1, tm.tm_mday,
			 wd_zh[tm.tm_wday]);
	else
		snprintf(date, sizeof(date), "%02d/%02d", tm.tm_mon + 1, tm.tm_mday);

	nova_round_rect_blend(fb, 0, 0, fb->w, NOVA_STATUSBAR_H, 0, 0x080a12, 140);
	nova_text_shadow(fb, 24, 12, clock, NOVA_WHITE, 2);
	dw = nova_text_width(clock, 2);
	nova_text(fb, 24 + dw + 18, 18, date, 0x9aa0b8, 1);

	bx = fb->w - 24 - 36;
	nova_round_rect(fb, bx, 15, 34, 16, 4, 0x9aa0b8);
	nova_round_rect(fb, bx + 2, 17, 24, 12, 3, NOVA_OK);
	nova_fill(fb, bx + 35, 19, 3, 8, 0x9aa0b8);
	for (int i = 0; i < 4; i++)
		nova_fill(fb, bx - 34 + i * 6, 26 - i * 4, 4, 4 + i * 4, 0xd6dbec);
}

void nova_back_button(NovaFB *fb, int cx, int cy, int r)
{
	nova_shadow(fb, cx - r, cy - r + 2, 2 * r, 2 * r, r, 8, 110);
	nova_circle(fb, cx, cy, r, 0x3b4266);
	nova_circle(fb, cx, cy - 2, r - 3, 0x2b3150);
	nova_line(fb, cx + r / 3, cy - r / 2, cx - r / 2, cy, NOVA_WHITE);
	nova_line(fb, cx - r / 2, cy, cx + r / 3, cy + r / 2, NOVA_WHITE);
	nova_line(fb, cx + r / 3, cy - r / 2, cx + r / 3, cy + r / 2, NOVA_WHITE);
}

void nova_app_header(NovaFB *fb, const char *title)
{
	char clock[16];

	nova_gradient(fb, 0, 0, fb->w, fb->h, 0x161b30, 0x0a0c14);
	nova_glow(fb, fb->w - 40, -30, 260, 0x6c5ce7, 46);
	nova_glow(fb, -40, fb->h + 30, 240, 0x2f7bff, 26);
	nova_clock(clock, sizeof(clock));
	nova_status_bar(fb, "mubaiOS", clock);
	nova_back_button(fb, 56, 96, 26);
	nova_text_shadow(fb, 104, 82, title, NOVA_WHITE, 3);
	nova_round_rect_blend(fb, 0, 130, fb->w, 2, 0, 0x2a3050, 120);
}

int nova_back_hit(int x, int y)
{
	return nova_hit(x, y, 26, 66, 62, 62);
}

int nova_hit(int px, int py, int x, int y, int w, int h)
{
	return px >= x && py >= y && px < x + w && py < y + h;
}

/* ------------------------------------------------------------------ */
/* input                                                               */
/* ------------------------------------------------------------------ */

int nova_input_open(NovaInput *in)
{
	memset(in, 0, sizeof(*in));
	in->abs_fd = in->rel_fd = in->kbd_fd = in->virt_fd = -1;
	in->abs_virtual = 0;

	for (int i = 0; i < 32 && in->nfds < 8; i++) {
		char path[64];
		snprintf(path, sizeof(path), "/dev/input/event%d", i);
		int fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
		if (fd < 0)
			continue;

		unsigned long evbits[EV_MAX / (8 * sizeof(long)) + 1] = {0};
		unsigned long keybits[KEY_MAX / (8 * sizeof(long)) + 1] = {0};
		ioctl(fd, EVIOCGBIT(0, sizeof(evbits)), evbits);
		ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keybits)), keybits);

		char name[80] = {0};
		int has_abs = evbits[EV_ABS / (8 * sizeof(long))] & (1UL << (EV_ABS % (8 * sizeof(long))));

		ioctl(fd, EVIOCGNAME(sizeof(name)), name);
		int has_rel = evbits[EV_REL / (8 * sizeof(long))] & (1UL << (EV_REL % (8 * sizeof(long))));
		int has_key = evbits[EV_KEY / (8 * sizeof(long))] & (1UL << (EV_KEY % (8 * sizeof(long))));

		/* The uinput touchscreen used for scripted taps must not shadow a
		 * real tablet/panel: prefer hardware, fall back to the virtual one. */
		int is_virtual = strstr(name, "mubaiOS virtual") != NULL;
		if (has_abs && is_virtual && in->virt_fd < 0 && in->abs_fd < 0) {
			in->virt_fd = fd;
			in->fds[in->nfds++] = fd;
			continue;
		}
		if (has_abs && !is_virtual && in->abs_fd < 0) {
			struct input_absinfo ai;
			in->abs_fd = fd;
			in->has_abs = 1;
			if (ioctl(fd, EVIOCGABS(ABS_X), &ai) == 0) {
				in->minx = ai.minimum;
				in->maxx = ai.maximum ? ai.maximum : 32767;
			} else {
				in->maxx = 32767;
			}
			if (ioctl(fd, EVIOCGABS(ABS_Y), &ai) == 0) {
				in->miny = ai.minimum;
				in->maxy = ai.maximum ? ai.maximum : 32767;
			} else {
				in->maxy = 32767;
			}
		} else if (has_rel && in->rel_fd < 0) {
			in->rel_fd = fd;
		} else if (has_key && !has_abs && !has_rel && in->kbd_fd < 0) {
			in->kbd_fd = fd;
		}
		in->fds[in->nfds++] = fd;
	}
	if (in->abs_fd < 0 && in->virt_fd >= 0) {
		struct input_absinfo ai;

		in->abs_fd = in->virt_fd;
		in->abs_virtual = 1;
		if (ioctl(in->virt_fd, EVIOCGABS(ABS_X), &ai) == 0) {
			in->minx = ai.minimum;
			in->maxx = ai.maximum ? ai.maximum : 32767;
		} else {
			in->maxx = 32767;
		}
		if (ioctl(in->virt_fd, EVIOCGABS(ABS_Y), &ai) == 0) {
			in->miny = ai.minimum;
			in->maxy = ai.maximum ? ai.maximum : 32767;
		} else {
			in->maxy = 32767;
		}
	}
	if (in->nfds == 0)
		return -1;
	in->x = g_screen_w / 2;
	in->y = g_screen_h / 2;
	return 0;
}

void nova_input_close(NovaInput *in)
{
	for (int i = 0; i < in->nfds; i++)
		close(in->fds[i]);
	in->nfds = 0;
}

static void queue_push(NovaInput *in, int type, int x, int y, int key, int value)
{
	int next = (in->qtail + 1) % 64;

	if (next == in->qhead)
		return;
	NovaEvent *e = &in->queue[in->qtail];
	e->type = type;
	e->x = x;
	e->y = y;
	e->key = key;
	e->value = value;
	in->qtail = next;
}

void nova_set_screen(int w, int h)
{
	g_screen_w = w;
	g_screen_h = h;
}

static int map_abs(int v, int min, int max, int size)
{
	if (max <= min)
		return 0;
	long r = (long)(v - min) * (size - 1) / (max - min);
	if (r < 0)
		r = 0;
	if (r >= size)
		r = size - 1;
	return (int)r;
}

static int clamp_int(int v, int lo, int hi)
{
	return v < lo ? lo : (v > hi ? hi : v);
}

static void process_event(NovaInput *in, const struct input_event *ev)
{
	switch (ev->type) {
	case EV_ABS:
		if (ev->code == ABS_X || ev->code == ABS_MT_POSITION_X) {
			in->x = map_abs(ev->value, in->minx, in->maxx, g_screen_w);
			in->moved = 1;
		} else if (ev->code == ABS_Y || ev->code == ABS_MT_POSITION_Y) {
			in->y = map_abs(ev->value, in->miny, in->maxy, g_screen_h);
			in->moved = 1;
		}
		break;
	case EV_REL:
		if (ev->code == REL_X) {
			in->x = clamp_int(in->x + ev->value * 2, 0, g_screen_w - 1);
			in->moved = 1;
		}
		if (ev->code == REL_Y) {
			in->y = clamp_int(in->y + ev->value * 2, 0, g_screen_h - 1);
			in->moved = 1;
		}
		if (ev->code == REL_WHEEL)
			in->wheel += ev->value;
		break;
	case EV_KEY:
		if (ev->code == BTN_TOUCH || ev->code == BTN_LEFT || ev->code == BTN_MOUSE) {
			if (ev->value) {
				in->down = 1;
				queue_push(in, NOVA_DOWN, in->x, in->y, 0, 1);
			} else {
				in->down = 0;
				queue_push(in, NOVA_UP, in->x, in->y, 0, 0);
			}
		} else if (ev->value) {
			queue_push(in, NOVA_KEY, in->x, in->y, ev->code, ev->value);
		}
		break;
	case EV_SYN:
		if (ev->code == SYN_REPORT) {
			if (in->moved)
				queue_push(in, NOVA_MOVE, in->x, in->y, 0, 0);
			in->moved = 0;
			while (in->wheel) {
				queue_push(in, NOVA_WHEEL, in->x, in->y, 0, in->wheel > 0 ? 1 : -1);
				in->wheel += in->wheel > 0 ? -1 : 1;
			}
		}
		break;
	default:
		break;
	}
}

int nova_peek(NovaInput *in, NovaEvent *ev)
{
	if (in->qhead == in->qtail)
		return 0;
	*ev = in->queue[in->qhead];
	return 1;
}

int nova_poll(NovaInput *in, NovaEvent *ev, int timeout_ms)
{
	if (in->qhead != in->qtail) {
		*ev = in->queue[in->qhead];
		in->qhead = (in->qhead + 1) % 64;
		return 1;
	}

	struct pollfd pfd[8];
	int n = in->nfds;

	for (int i = 0; i < n; i++) {
		pfd[i].fd = in->fds[i];
		pfd[i].events = POLLIN;
		pfd[i].revents = 0;
	}
	int r = poll(pfd, (nfds_t)n, timeout_ms);
	if (r <= 0)
		return 0;

	for (int i = 0; i < n; i++) {
		if (!(pfd[i].revents & POLLIN))
			continue;
		for (;;) {
			struct input_event iev;
			ssize_t got = read(pfd[i].fd, &iev, sizeof(iev));
			if (got != (ssize_t)sizeof(iev))
				break;
			process_event(in, &iev);
		}
	}
	if (in->qhead != in->qtail) {
		*ev = in->queue[in->qhead];
		in->qhead = (in->qhead + 1) % 64;
		return 1;
	}
	return 0;
}

/* ------------------------------------------------------------------ */
/* keyboard mapping (Linux keycodes -> ASCII)                          */
/* ------------------------------------------------------------------ */

/* ------------------------------------------------------------------ */
/* pointer cursor (save/restore so apps can move it without repainting) */
/* ------------------------------------------------------------------ */

static uint32_t cursor_bg[24 * 24];
static int cursor_bg_x, cursor_bg_y, cursor_bg_valid;

void nova_cursor_reset(void)
{
	cursor_bg_valid = 0;
}

void nova_cursor_draw(NovaFB *fb, int x, int y)
{
	int had_bg = cursor_bg_valid, old_x = cursor_bg_x, old_y = cursor_bg_y;
	int was_dirty = fb_dirty;

	if (cursor_bg_valid) {
		for (int dy = 0; dy < 24; dy++)
			for (int dx = 0; dx < 24; dx++)
				nova_pixel(fb, cursor_bg_x + dx, cursor_bg_y + dy,
					   cursor_bg[dy * 24 + dx]);
		cursor_bg_valid = 0;
	}
	for (int dy = 0; dy < 24; dy++)
		for (int dx = 0; dx < 24; dx++)
			cursor_bg[dy * 24 + dx] = nova_get(fb, x - 9 + dx, y - 9 + dy);
	cursor_bg_x = x - 9;
	cursor_bg_y = y - 9;
	cursor_bg_valid = 1;
	nova_circle(fb, x, y, 9, 0xffe066);
	nova_circle(fb, x, y, 6, 0x6c5ce7);
	if (was_dirty && dirty_valid) {
		int bx0 = dirty_x0 - 10 < 0 ? 0 : dirty_x0 - 10;
		int by0 = dirty_y0 - 10 < 0 ? 0 : dirty_y0 - 10;
		int bx1 = dirty_x1 + 10 >= fb->w ? fb->w : dirty_x1 + 11;
		int by1 = dirty_y1 + 10 >= fb->h ? fb->h : dirty_y1 + 11;

		nova_flush_rect(fb, bx0, by0, bx1 - bx0, by1 - by0);
		fb_dirty = 0;
		dirty_clear();
	} else if (was_dirty) {
		nova_flush(fb);
	} else {
		if (had_bg)
			nova_flush_rect(fb, old_x, old_y, 24, 24);
		nova_flush_rect(fb, x - 9, y - 9, 24, 24);
	}
}

int nova_key_ascii(int code, int shift)
{
	static const char letters[26] = "qwertyuiopasdfghjklzxcvbnm";
	static const int letter_codes[26] = {
		16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
		30, 31, 32, 33, 34, 35, 36, 37, 38,
		44, 45, 46, 47, 48, 49, 50,
	};
	static const char digits[10] = "1234567890";
	static const int digit_codes[10] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11};

	if (code == 28)
		return '\n';
	if (code == 57)
		return ' ';
	if (code == 14)
		return 8;
	if (code == 12)
		return shift ? '_' : '-';
	if (code == 13)
		return shift ? '+' : '=';
	if (code == 51)
		return shift ? '<' : ',';
	if (code == 52)
		return shift ? '>' : '.';
	if (code == 53)
		return shift ? '?' : '/';
	if (code == 40)
		return shift ? '~' : '\'';
	if (code == 26)
		return shift ? '^' : '[';

	for (int i = 0; i < 26; i++)
		if (code == letter_codes[i])
			return shift ? (char)(letters[i] - 32) : letters[i];
	for (int i = 0; i < 10; i++)
		if (code == digit_codes[i]) {
			static const char sym[10] = "!@#$%^&*()";
			return shift ? sym[i] : digits[i];
		}
	return 0;
}

/* ---------------- soft & translucent primitives ---------------- */

uint32_t nova_mix(uint32_t a, uint32_t b, int t)
{
	int ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
	int br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;

	if (t <= 0)
		return a;
	if (t >= 255)
		return b;
	ar += (br - ar) * t / 255;
	ag += (bg - ag) * t / 255;
	ab += (bb - ab) * t / 255;
	return (uint32_t)((ar << 16) | (ag << 8) | ab);
}

void nova_blend_px(NovaFB *fb, int x, int y, uint32_t c, int alpha)
{
	if (alpha <= 0 || x < 0 || y < 0 || x >= fb->w || y >= fb->h)
		return;
	if (alpha >= 255) {
		put_px(fb, x, y, c);
		return;
	}
	put_px(fb, x, y, nova_mix(nova_get(fb, x, y), c, alpha));
}

static int rect_inset(int r, int dy)
{
	if (r <= 0 || dy >= r)
		return 0;
	return r - isqrt_i(r * r - (r - dy) * (r - dy));
}

void nova_round_rect_blend(NovaFB *fb, int x, int y, int w, int h, int r,
			   uint32_t c, int alpha)
{
	if (r * 2 > w)
		r = w / 2;
	if (r * 2 > h)
		r = h / 2;
	for (int dy = 0; dy < h; dy++) {
		int inset = dy < r ? rect_inset(r, dy)
			  : (dy >= h - r ? rect_inset(r, h - 1 - dy) : 0);

		for (int dx = inset; dx < w - inset; dx++)
			nova_blend_px(fb, x + dx, y + dy, c, alpha);
	}
}

void nova_shadow(NovaFB *fb, int x, int y, int w, int h, int r, int blur, int alpha)
{
	for (int i = blur; i > 0; i--) {
		int a = alpha * (blur - i + 1) / (blur + 1);

		if (a > 0)
			nova_round_rect_blend(fb, x - i, y - i, w + 2 * i, h + 2 * i,
					      r + i, 0x000000, a);
	}
}

void nova_glow(NovaFB *fb, int cx, int cy, int r, uint32_t c, int alpha)
{
	int r2 = r * r;

	for (int y = cy - r; y <= cy + r; y++) {
		if (y < 0 || y >= fb->h)
			continue;
		for (int x = cx - r; x <= cx + r; x++) {
			int dx, dy, a, d2;

			if (x < 0 || x >= fb->w)
				continue;
			dx = x - cx;
			dy = y - cy;
			d2 = dx * dx + dy * dy;
			if (d2 > r2)
				continue;
			a = alpha * (r2 - d2) / r2;
			a = a * a / 255;
			if (a > 0)
				nova_blend_px(fb, x, y, c, a);
		}
	}
}

void nova_squircle(NovaFB *fb, int x, int y, int w, int h,
		   uint32_t top, uint32_t bottom)
{
	int r = w * 30 / 100;

	nova_round_rect_gradient(fb, x, y, w, h, r, top, bottom);
	nova_round_rect_blend(fb, x + w / 8, y + h / 16, w - w / 4, h / 4,
			      r - r / 2, 0xffffff, 9);
}

void nova_text_shadow(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale)
{
	int off = scale > 2 ? 2 : 1;

	nova_text(fb, x + off, y + off, s, 0x07080f, scale);
	nova_text(fb, x, y, s, color, scale);
}
