/*
 * 2048 -- arrow keys slide and merge tiles.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static int board[4][4];
static int score, best, over;
static int px = 400, py = 300;

static void spawn(void)
{
	int empty[16], n = 0;

	for (int y = 0; y < 4; y++)
		for (int x = 0; x < 4; x++)
			if (!board[x][y])
				empty[n++] = y * 4 + x;
	if (!n)
		return;
	int pick = empty[rand() % n];
	board[pick % 4][pick / 4] = (rand() % 10 == 0) ? 4 : 2;
}

static void reset(void)
{
	memset(board, 0, sizeof(board));
	score = 0;
	over = 0;
	spawn();
	spawn();
}

static int slide(int dir)   /* 0 left, 1 right, 2 up, 3 down */
{
	int moved = 0;

	for (int line = 0; line < 4; line++) {
		int vals[4], n = 0;

		for (int i = 0; i < 4; i++) {
			int x = dir == 0 ? i : dir == 1 ? 3 - i : line;
			int y = dir == 2 ? i : dir == 3 ? 3 - i : line;
			if (board[x][y])
				vals[n++] = board[x][y];
		}
		int out[4] = {0}, m = 0;
		for (int i = 0; i < n; i++) {
			if (i + 1 < n && vals[i] == vals[i + 1]) {
				out[m++] = vals[i] * 2;
				score += vals[i] * 2;
				i++;
			} else {
				out[m++] = vals[i];
			}
		}
		for (int i = 0; i < 4; i++) {
			int x = dir == 0 ? i : dir == 1 ? 3 - i : line;
			int y = dir == 2 ? i : dir == 3 ? 3 - i : line;
			if (board[x][y] != out[i])
				moved = 1;
			board[x][y] = out[i];
		}
	}
	return moved;
}

static int can_move(void)
{
	for (int y = 0; y < 4; y++)
		for (int x = 0; x < 4; x++) {
			if (!board[x][y])
				return 1;
			if (x < 3 && board[x][y] == board[x + 1][y])
				return 1;
			if (y < 3 && board[x][y] == board[x][y + 1])
				return 1;
		}
	return 0;
}

static uint32_t tile_color(int v)
{
	switch (v) {
	case 2: return 0xeee4da;
	case 4: return 0xede0c8;
	case 8: return 0xf2b179;
	case 16: return 0xf59563;
	case 32: return 0xf67c5f;
	case 64: return 0xf65e3b;
	case 128: return 0xedcf72;
	case 256: return 0xedcc61;
	case 512: return 0xedc850;
	case 1024: return 0xedc53f;
	case 2048: return 0xedc22e;
	default: return 0x3c3a32;
	}
}

static void draw(NovaFB *fb)
{
	char buf[32];
	int cell = 150, gap = 14;
	int ox = (fb->w - (4 * cell + 3 * gap)) / 2, oy = 180;

	nova_app_header(fb, "2048");
	snprintf(buf, sizeof(buf), L("得分 %d   最高 %d", "Score %d  Best %d"), score, best);
	nova_text(fb, 60, 132, buf, NOVA_DIM, 2);

	nova_round_rect(fb, ox - 12, oy - 12, 4 * cell + 3 * gap + 24, 4 * cell + 3 * gap + 24, 16, 0x1b2030);
	for (int y = 0; y < 4; y++) {
		for (int x = 0; x < 4; x++) {
			int cx = ox + x * (cell + gap), cy = oy + y * (cell + gap);

			nova_round_rect(fb, cx, cy, cell, cell, 12, 0x232838);
			if (board[x][y]) {
				nova_round_rect(fb, cx, cy, cell, cell, 12, tile_color(board[x][y]));
				snprintf(buf, sizeof(buf), "%d", board[x][y]);
				nova_text_center(fb, cx + cell / 2, cy + 58, buf,
						 board[x][y] > 4 ? NOVA_WHITE : 0x776e65, 3);
			}
		}
	}

	if (over) {
		nova_round_rect(fb, fb->w / 2 - 220, 360, 440, 110, 18, 0x000000);
		nova_text_center(fb, fb->w / 2, 390, "游戏结束", NOVA_WHITE, 3);
		nova_text_center(fb, fb->w / 2, 434, "点「重来」继续", NOVA_DIM, 1);
	}
	nova_round_rect(fb, fb->w / 2 - 110, 740, 220, 52, 14, 0x2a2f40);
	nova_text_center(fb, fb->w / 2, 752, "重来", NOVA_WHITE, 2);
	nova_text_center(fb, fb->w / 2, 700, "方向键移动", 0x4a5068, 1);
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

	srand((unsigned)time(NULL));
	reset();
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
		if (ev.type == NOVA_KEY) {
			int dir = -1;

			if (ev.key == 1)
				return 0;
			if (ev.key == 105) dir = 0;
			if (ev.key == 106) dir = 1;
			if (ev.key == 103) dir = 2;
			if (ev.key == 108) dir = 3;
			if (dir >= 0 && !over) {
				if (slide(dir)) {
					spawn();
					if (score > best)
						best = score;
					if (!can_move())
						over = 1;
				}
			}
			nova_cursor_reset();
			draw(&fb);
			nova_cursor_draw(&fb, px, py);
			continue;
		}
		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y))
				return 0;
			if (nova_hit(ev.x, ev.y, fb.w / 2 - 110, 740, 220, 52)) {
				reset();
				nova_cursor_reset();
				draw(&fb);
				nova_cursor_draw(&fb, px, py);
			}
		}
	}
}
