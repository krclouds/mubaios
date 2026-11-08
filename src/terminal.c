/*
 * Terminal -- run commands from the mubaiOS shell, rendered into the
 * framebuffer.  Works with a physical keyboard and with the on-screen
 * keyboard, so it is usable on a pure touch device (or when the QEMU
 * window does not have keyboard focus).
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "nova.h"

#define MAX_LINES 64
#define LINE_LEN 160
#define KB_HEIGHT 360
#define KEY_H 54
#define KEY_GAP 6

enum { K_CHAR, K_SHIFT, K_SPACE, K_BACK, K_ENTER };

struct key {
	int x, y, w, h;
	int action;
	char label[8];
	char ch;
};

static struct key keys[80];
static int key_count;

static char lines[MAX_LINES][LINE_LEN];
static int line_count;
static char input[LINE_LEN];
static int input_len;
static int kb_visible;
static int shift;
static int ptr_x = 400, ptr_y = 300;
static NovaFB *g_fb;

static void add_line(const char *s)
{
	int idx;

	if (line_count < MAX_LINES) {
		idx = line_count++;
	} else {
		memmove(lines[0], lines[1], sizeof(lines[0]) * (MAX_LINES - 1));
		idx = MAX_LINES - 1;
	}
	snprintf(lines[idx], LINE_LEN, "%s", s);
}

static void run_command(const char *cmd)
{
	char full[LINE_LEN + 32];
	char buf[LINE_LEN];
	FILE *p;

	snprintf(full, sizeof(full), "%s 2>&1", cmd);
	p = popen(full, "r");
	if (!p) {
		add_line("sh: 无法启动命令");
		return;
	}
	while (fgets(buf, sizeof(buf), p)) {
		buf[strcspn(buf, "\n")] = '\0';
		add_line(buf);
	}
	pclose(p);
}

static int input_box_y(void)
{
	return kb_visible ? g_fb->h - KB_HEIGHT - 84 : g_fb->h - 104;
}

static void add_key(int x, int y, int w, int h, int action, const char *label, char ch)
{
	struct key *k = &keys[key_count++];

	k->x = x;
	k->y = y;
	k->w = w;
	k->h = h;
	k->action = action;
	snprintf(k->label, sizeof(k->label), "%s", label);
	k->ch = ch;
}

static void draw_keyboard(NovaFB *fb)
{
	static const char *rows[] = {"1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"};
	int top = fb->h - KB_HEIGHT;
	int total = 10 * 96 + 9 * KEY_GAP;
	int left = (fb->w - total) / 2;

	key_count = 0;
	for (int r = 0; r < 4; r++) {
		int n = (int)strlen(rows[r]);
		int row_w = n * 96 + (n - 1) * KEY_GAP;
		int x0 = (fb->w - row_w) / 2;
		int y = top + 12 + r * (KEY_H + KEY_GAP);

		for (int i = 0; i < n; i++) {
			char label[2] = {rows[r][i], 0};
			char ch = rows[r][i];
			if (shift && ch >= 'a' && ch <= 'z')
				label[0] = (char)(ch - 32);
			add_key(x0 + i * (96 + KEY_GAP), y, 96, KEY_H, K_CHAR, label,
				shift ? (char)((ch >= 'a' && ch <= 'z') ? ch - 32 : ch) : ch);
		}
	}

	int by = top + 12 + 4 * (KEY_H + KEY_GAP);
	int bw = 150, space_w = 380;
	int total_b = bw + KEY_GAP + space_w + KEY_GAP + bw + KEY_GAP + bw;
	int bx = (fb->w - total_b) / 2;
	int kx = bx;

	add_key(kx, by, bw, KEY_H, K_SHIFT, shift ? "大写" : "小写", 0);
	kx += bw + KEY_GAP;
	add_key(kx, by, space_w, KEY_H, K_SPACE, "空格", ' ');
	kx += space_w + KEY_GAP;
	add_key(kx, by, bw, KEY_H, K_BACK, "退格", 0);
	kx += bw + KEY_GAP;
	add_key(kx, by, bw, KEY_H, K_ENTER, "回车", 0);
	(void)left;

	for (int i = 0; i < key_count; i++) {
		struct key *k = &keys[i];
		uint32_t bg = (k->action == K_ENTER) ? 0x2ecc71 :
			      (k->action == K_BACK || k->action == K_SHIFT) ? 0x2a2f40 : 0x1b2030;

		nova_round_rect(fb, k->x, k->y, k->w, k->h, 12, bg);
		nova_text_center(fb, k->x + k->w / 2, k->y + (KEY_H - 32) / 2, k->label,
				 k->action == K_ENTER ? 0x08130c : NOVA_WHITE, 2);
	}
}

static void draw_input(NovaFB *fb)
{
	int box_y = input_box_y();

	nova_round_rect(fb, 40, box_y, fb->w - 80, 64, 14, 0x1b2030);
	nova_text(fb, 64, box_y + 18, "mubaios:/#", NOVA_OK, 2);
	nova_text(fb, 64 + 16 * 8, box_y + 18, input, NOVA_WHITE, 2);
	if ((line_count + input_len) % 2 == 0) {
		int cx = 64 + 16 * 8 + nova_text_width(input, 2);
		nova_fill(fb, cx + 2, box_y + 16, 3, 32, NOVA_ACCENT);
	}
}

static void draw(NovaFB *fb)
{
	nova_cursor_reset();
	nova_app_header(fb, "终端");

	nova_round_rect(fb, fb->w - 180, 66, 160, 60, 16, kb_visible ? 0x2ecc71 : 0x2a2f40);
	nova_text_center(fb, fb->w - 100, 84, "键盘", kb_visible ? 0x08130c : NOVA_WHITE, 2);

	int y = 150;
	int bottom = (kb_visible ? fb->h - KB_HEIGHT : fb->h - 120) - 16;
	int visible = (bottom - y) / 34;

	if (line_count > visible)
		visible = line_count - visible;
	else
		visible = 0;

	for (int i = visible; i < line_count; i++) {
		nova_text(fb, 60, y, lines[i], 0xc8f0c8, 2);
		y += 34;
	}

	draw_input(fb);

	if (kb_visible)
		draw_keyboard(fb);
}

static void execute_input(void)
{
	char echo[LINE_LEN];

	input[input_len] = '\0';
	if (input_len == 0)
		return;
	snprintf(echo, sizeof(echo), "mubaios:/# %s", input);
	add_line(echo);
	run_command(input);
	input_len = 0;
	input[0] = '\0';
}

static void press_key(const struct key *k)
{
	switch (k->action) {
	case K_CHAR:
		if (input_len < LINE_LEN - 2) {
			input[input_len++] = k->ch;
			input[input_len] = '\0';
		}
		break;
	case K_SPACE:
		if (input_len < LINE_LEN - 2) {
			input[input_len++] = ' ';
			input[input_len] = '\0';
		}
		break;
	case K_BACK:
		if (input_len > 0)
			input[--input_len] = '\0';
		break;
	case K_SHIFT:
		shift = !shift;
		break;
	case K_ENTER:
		execute_input();
		break;
	}
}

int main(void)
{
	static NovaFB framebuffer;
	NovaInput in;
	NovaEvent ev;

	g_fb = &framebuffer;
	if (nova_fb_open(g_fb) < 0)
		return 1;
	nova_set_screen(g_fb->w, g_fb->h);
	if (nova_input_open(&in) < 0)
		return 1;

	add_line("mubaiOS 0.1 终端");
	add_line("命令经由 /bin/sh (BusyBox) 执行");
	add_line("试试：uname -a、ls /apps、free");
	add_line("没有实体键盘时，点右上角「键盘」用鼠标输入");
	draw(g_fb);
	nova_cursor_draw(g_fb, ptr_x, ptr_y);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		ptr_x = ev.x;
		ptr_y = ev.y;

		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(g_fb, ev.x, ev.y);
			continue;
		}

		if (ev.type == NOVA_KEY) {
			if (ev.key == 1)
				return 0;
			if (ev.key == 42 || ev.key == 54) {
				shift = ev.value ? 1 : 0;
				continue;
			}
			if (ev.key == 28) {
				execute_input();
			} else if (ev.key == 14) {
				if (input_len > 0)
					input[--input_len] = '\0';
			} else {
				char c = (char)nova_key_ascii(ev.key, shift);
				if (c && input_len < LINE_LEN - 2) {
					input[input_len++] = c;
					input[input_len] = '\0';
				}
			}
			draw(g_fb);
			nova_cursor_draw(g_fb, ptr_x, ptr_y);
			continue;
		}

		if (ev.type != NOVA_DOWN)
			continue;

		if (nova_back_hit(ev.x, ev.y))
			return 0;

		if (nova_hit(ev.x, ev.y, g_fb->w - 180, 66, 160, 60)) {
			kb_visible = !kb_visible;
			draw(g_fb);
			nova_cursor_draw(g_fb, ptr_x, ptr_y);
			continue;
		}

		if (kb_visible) {
			int hit = 0, action = -1;
			for (int i = 0; i < key_count; i++) {
				if (nova_hit(ev.x, ev.y, keys[i].x, keys[i].y, keys[i].w, keys[i].h)) {
					action = keys[i].action;
					press_key(&keys[i]);
					hit = 1;
					break;
				}
			}
			if (hit) {
				if (action == K_ENTER || action == K_SHIFT)
					draw(g_fb);
				else
					draw_input(g_fb);
				nova_cursor_draw(g_fb, ptr_x, ptr_y);
			}
		}
	}
}
