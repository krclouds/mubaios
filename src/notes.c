/*
 * Notes -- a plain text notepad with a small pinyin input method.
 *
 * Type latin letters, press Space (or 1..9) to commit a character, Enter for a
 * new line, Backspace to erase, Esc to save and leave.  The syllable table is
 * generated from Unihan readings over the GB2312 level-1 character set, so the
 * candidate lists stay short and the characters are the common ones.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "nova.h"
#include "pinyin.h"

#define MAXCH 4096
#define MAXPY 24

static char text[MAXCH];
static int len;
static char py[MAXPY];
static int py_len;
static const char *cands[9];
static int prefix_len;

static const struct { const char *py, *word; } words[] = {
	{"nihao", "你好"}, {"shijie", "世界"}, {"zhongwen", "中文"},
	{"xiexie", "谢谢"}, {"zaijian", "再见"}, {"woshi", "我是"},
	{"nishi", "你是"}, {"ceshi", "测试"}, {"bianqian", "便签"},
	{"shurufa", "输入法"}, {"diannao", "电脑"}, {"xiexie", "谢谢"},
};
static int cand_n;
static int px = 400, py_pos = 300;

static void load(void)
{
	int fd = open("/data/note.txt", O_RDONLY);

	if (fd < 0)
		return;
	len = (int)read(fd, text, MAXCH - 1);
	if (len < 0)
		len = 0;
	text[len] = 0;
	close(fd);
}

static void save(void)
{
	int fd = open("/data/note.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);

	if (fd < 0)
		return;
	(void)!write(fd, text, (size_t)len);
	close(fd);
}

static int utf8_len(unsigned char c)
{
	if (c < 0x80)
		return 1;
	if ((c & 0xe0) == 0xc0)
		return 2;
	if ((c & 0xf0) == 0xe0)
		return 3;
	return 4;
}

static void update_candidates(void)
{
	cand_n = 0;
	prefix_len = 0;
	for (size_t w = 0; w < sizeof(words) / sizeof(words[0]); w++) {
		if (strcmp(words[w].py, py) == 0) {
			cands[0] = words[w].word;
			cand_n = 1;
			prefix_len = py_len;
			return;
		}
	}
	for (int pl = py_len; pl >= 1; pl--) {
		char syl[16];
		struct pinyin_entry const *hit = NULL;

		if (pl >= (int)sizeof(syl))
			continue;
		memcpy(syl, py, (size_t)pl);
		syl[pl] = 0;
		for (int i = 0; i < PINYIN_N; i++)
			if (strcmp(pinyin_table[i].py, syl) == 0) {
				hit = &pinyin_table[i];
				break;
			}
		if (!hit)
			continue;
		prefix_len = pl;
		{
			const char *p = hit->chars;

			while (*p && cand_n < 9) {
				int n = utf8_len((unsigned char)*p);
				static char store[9][8];

				memcpy(store[cand_n], p, (size_t)n);
				store[cand_n][n] = 0;
				cands[cand_n] = store[cand_n];
				cand_n++;
				p += n;
			}
		}
		return;
	}
	for (int i = 0; i < PINYIN_N; i++) {
		if (strcmp(pinyin_table[i].py, py) != 0)
			continue;
		const char *p = pinyin_table[i].chars;

		while (*p && cand_n < 9) {
			int n = utf8_len((unsigned char)*p);
			static char store[9][8];

			memcpy(store[cand_n], p, (size_t)n);
			store[cand_n][n] = 0;
			cands[cand_n] = store[cand_n];
			cand_n++;
			p += n;
		}
		return;
	}
}

static void commit(const char *s)
{
	int n = (int)strlen(s);

	if (len + n < MAXCH - 1) {
		memcpy(text + len, s, (size_t)n);
		len += n;
		text[len] = 0;
	}
	if (prefix_len > 0 && prefix_len <= py_len) {
		memmove(py, py + prefix_len, (size_t)(py_len - prefix_len + 1));
		py_len -= prefix_len;
	} else {
		py_len = 0;
		py[0] = 0;
	}
	prefix_len = 0;
	cand_n = 0;
	if (py_len)
		update_candidates();
}

static void backspace(void)
{
	if (py_len > 0) {
		py[--py_len] = 0;
		update_candidates();
		return;
	}
	if (len > 0) {
		int i = len - 1;

		while (i > 0 && ((unsigned char)text[i] & 0xc0) == 0x80)
			i--;
		len = i;
		text[len] = 0;
	}
}

static void draw(NovaFB *fb)
{
	int bx = 60, by = 155, bw = fb->w - 120, bh = fb->h - 250;
	int x = bx + 30, y = by + 26, line_h = 34;
	char buf[8];

	nova_app_header(fb, "便签");
	nova_text(fb, 60, 132, "拼音输入：字母 + 空格 / 数字选字 · Esc 保存退出", NOVA_DIM, 1);
	nova_round_rect(fb, bx, by, bw, bh, 16, 0x1b2030);

	int i = 0;
	while (i < len) {
		int n = utf8_len((unsigned char)text[i]);

		if (text[i] == '\n') {
			x = bx + 30;
			y += line_h;
			i++;
			continue;
		}
		int w = (n == 1) ? 16 : 32;

		if (x + w > bx + bw - 30) {
			x = bx + 30;
			y += line_h;
		}
		if (y > by + bh - 60)
			break;
		memcpy(buf, text + i, (size_t)n);
		buf[n] = 0;
		nova_text(fb, x, y, buf, NOVA_TEXT, 2);
		x += w;
		i += n;
	}
	if (len == 0 && py_len == 0)
		nova_text(fb, bx + 30, by + 26, "直接输入即可，支持拼音打中文", 0x4a5068, 2);

	if (py_len) {
		nova_text(fb, x, y, py, 0xf1c40f, 2);
		x += py_len * 16;
	}

	if (cand_n > 0) {
		int cy = by + bh - 54;

		nova_fill(fb, bx + 1, cy - 6, bw - 2, 52, 0x141821);
		int cx = bx + 24;
		for (int k = 0; k < cand_n; k++) {
			snprintf(buf, sizeof(buf), "%d", k + 1);
			nova_text(fb, cx, cy + 8, buf, NOVA_DIM, 1);
			nova_text(fb, cx + 14, cy, cands[k], k == 0 ? 0xf1c40f : NOVA_WHITE, 2);
			cx += 14 + 32 + 18;
		}
	}
	nova_cursor_draw(fb, px, py_pos);
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

	load();
	nova_cursor_reset();
	draw(&fb);
	nova_cursor_draw(&fb, px, py_pos);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		px = ev.x;
		py_pos = ev.y;

		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY) {
			if (ev.key == 1) {
				save();
				return 0;
			}
			if (ev.key == 14) {
				backspace();
			} else if (ev.key == 28) {
				if (len < MAXCH - 1) {
					text[len++] = '\n';
					text[len] = 0;
				}
			} else if (ev.key == 57) {
				if (cand_n > 0)
					commit(cands[0]);
				else if (len < MAXCH - 1) {
					text[len++] = ' ';
					text[len] = 0;
				}
			} else if (ev.key >= 2 && ev.key <= 10 && cand_n > 0) {
				int k = ev.key - 2;

				if (k < cand_n)
					commit(cands[k]);
			} else {
				char c = (char)nova_key_ascii(ev.key, 0);

				if (c >= 'a' && c <= 'z' && py_len < MAXPY - 1) {
					py[py_len++] = c;
					py[py_len] = 0;
					update_candidates();
				} else if (c && py_len == 0 && len < MAXCH - 1) {
					text[len++] = c;
					text[len] = 0;
				}
			}
			nova_cursor_reset();
			draw(&fb);
			nova_cursor_draw(&fb, px, py_pos);
			continue;
		}
		if (ev.type == NOVA_DOWN && nova_back_hit(ev.x, ev.y)) {
			save();
			return 0;
		}
	}
}
