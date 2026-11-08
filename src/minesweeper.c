/*
 * Minesweeper -- 10x10, 15 mines, tap to open, flag mode for marking.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

#define N 10
#define MINES 15
#define CELL 56

static unsigned char mine[N][N], open_[N][N], flag[N][N];
static int flag_mode, over, won, opened;
static int px = 400, py = 300;

static int neighbours(int x, int y)
{
	int c = 0;

	for (int dy = -1; dy <= 1; dy++)
		for (int dx = -1; dx <= 1; dx++) {
			int nx = x + dx, ny = y + dy;
			if ((dx || dy) && nx >= 0 && ny >= 0 && nx < N && ny < N && mine[nx][ny])
				c++;
		}
	return c;
}

static void reset(void)
{
	memset(mine, 0, sizeof(mine));
	memset(open_, 0, sizeof(open_));
	memset(flag, 0, sizeof(flag));
	over = won = opened = 0;
	flag_mode = 0;
	srand((unsigned)time(NULL));
	for (int placed = 0; placed < MINES;) {
		int x = rand() % N, y = rand() % N;
		if (!mine[x][y]) {
			mine[x][y] = 1;
			placed++;
		}
	}
}

static void open_cell(int x, int y)
{
	if (x < 0 || y < 0 || x >= N || y >= N || open_[x][y] || flag[x][y])
		return;
	open_[x][y] = 1;
	opened++;
	if (mine[x][y]) {
		over = 1;
		return;
	}
	if (neighbours(x, y) == 0)
		for (int dy = -1; dy <= 1; dy++)
			for (int dx = -1; dx <= 1; dx++)
				if (dx || dy)
					open_cell(x + dx, y + dy);
}

static void draw(NovaFB *fb)
{
	char buf[32];
	int ox = (fb->w - N * CELL) / 2, oy = 170;

	nova_app_header(fb, "扫雷");
	snprintf(buf, sizeof(buf), L("已开 %d/%d   %s", "Opened %d/%d   %s"), opened, N * N - MINES,
		 flag_mode ? L("标记模式", "Flag mode") : L("挖掘模式", "Dig mode"));
	nova_text(fb, 60, 132, buf, NOVA_DIM, 2);

	for (int y = 0; y < N; y++) {
		for (int x = 0; x < N; x++) {
			int cx = ox + x * CELL, cy = oy + y * CELL;
			uint32_t bg = 0x2a2f40;

			if (open_[x][y])
				bg = mine[x][y] ? 0x922b21 : 0x171b26;
			if (flag[x][y])
				bg = 0x7d6608;
			nova_round_rect(fb, cx + 2, cy + 2, CELL - 4, CELL - 4, 6, bg);
			if (open_[x][y] && !mine[x][y]) {
				int c = neighbours(x, y);
				if (c) {
					snprintf(buf, sizeof(buf), "%d", c);
					nova_text_center(fb, cx + CELL / 2, cy + 14, buf,
							 c == 1 ? 0x3498db : c == 2 ? 0x2ecc71 : 0xe74c3c, 2);
				}
			}
			if (open_[x][y] && mine[x][y])
				nova_circle(fb, cx + CELL / 2, cy + CELL / 2, 14, 0x000000);
			if (flag[x][y])
				nova_text_center(fb, cx + CELL / 2, cy + 14, "旗", 0xf1c40f, 2);
		}
	}

	nova_round_rect(fb, 60, 740, 220, 52, 14, flag_mode ? 0x7d6608 : 0x2a2f40);
	nova_text_center(fb, 170, 752, L("切换标记", "Flag mode"), NOVA_WHITE, 2);
	nova_round_rect(fb, fb->w - 280, 740, 220, 52, 14, 0x2a2f40);
	nova_text_center(fb, fb->w - 170, 752, "重来", NOVA_WHITE, 2);

	if (over || won) {
		nova_round_rect(fb, fb->w / 2 - 220, 330, 440, 120, 20, 0x000000);
		nova_text_center(fb, fb->w / 2, 360, won ? "扫雷成功" : "踩到地雷", NOVA_WHITE, 3);
		nova_text_center(fb, fb->w / 2, 410, "点「重来」再开一局", NOVA_DIM, 1);
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
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;
		if (ev.type != NOVA_DOWN)
			continue;
		if (nova_back_hit(ev.x, ev.y))
			return 0;
		if (nova_hit(ev.x, ev.y, 60, 740, 220, 52)) {
			flag_mode = !flag_mode;
		} else if (nova_hit(ev.x, ev.y, fb.w - 280, 740, 220, 52)) {
			reset();
		} else {
			int ox = (fb.w - N * CELL) / 2, oy = 170;
			int x = (ev.x - ox) / CELL, y = (ev.y - oy) / CELL;
			if (x >= 0 && y >= 0 && x < N && y < N && !over && !won) {
				if (flag_mode) {
					if (!open_[x][y])
						flag[x][y] = !flag[x][y];
				} else {
					open_cell(x, y);
					if (opened == N * N - MINES && !over)
						won = 1;
				}
			}
		}
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
