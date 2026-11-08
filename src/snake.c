/*
 * Snake -- a small game, installed from the mubaiOS app store.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

#define COLS 58
#define ROWS 26
#define CELL 20
#define OX 60
#define OY 140

static int snake_x[COLS * ROWS], snake_y[COLS * ROWS];
static int snake_len;
static int dir_x = 1, dir_y = 0;
static int food_x, food_y;
static int score, best, dead;
static int ptr_x = 400, ptr_y = 400;

static void reset(void)
{
	snake_len = 4;
	for (int i = 0; i < snake_len; i++) {
		snake_x[i] = 6 - i;
		snake_y[i] = ROWS / 2;
	}
	dir_x = 1;
	dir_y = 0;
	score = 0;
	dead = 0;
	srand((unsigned)time(NULL));
	food_x = 10 + rand() % (COLS - 12);
	food_y = 4 + rand() % (ROWS - 6);
}

static void draw(NovaFB *fb)
{
	char buf[64];

	nova_cursor_reset();
	nova_app_header(fb, "贪吃蛇");

	snprintf(buf, sizeof(buf), L("得分 %d   最高 %d", "Score %d  Best %d"), score, best);
	nova_text(fb, 60, 146, buf, NOVA_TEXT, 2);
	nova_round_rect(fb, OX - 10, OY - 10, COLS * CELL + 20, ROWS * CELL + 20, 14, 0x0b0d14);

	for (int i = 0; i < snake_len; i++) {
		uint32_t c = (i == 0) ? 0x2ecc71 : 0x27ae60;
		nova_round_rect(fb, OX + snake_x[i] * CELL + 1, OY + snake_y[i] * CELL + 1,
				CELL - 2, CELL - 2, 5, c);
	}
	nova_circle(fb, OX + food_x * CELL + CELL / 2, OY + food_y * CELL + CELL / 2, CELL / 2 - 2, 0xe74c3c);

	if (dead) {
		nova_fill(fb, OX, OY, COLS * CELL, ROWS * CELL, 0x000000);
		nova_text_center(fb, OX + COLS * CELL / 2, OY + ROWS * CELL / 2 - 60, "游戏结束", NOVA_WHITE, 4);
		nova_text_center(fb, OX + COLS * CELL / 2, OY + ROWS * CELL / 2 + 10, "点击重新开始", NOVA_DIM, 2);
	}
	nova_cursor_draw(fb, ptr_x, ptr_y);
}

static void step(void)
{
	int nx = snake_x[0] + dir_x;
	int ny = snake_y[0] + dir_y;

	if (nx < 0 || ny < 0 || nx >= COLS || ny >= ROWS)
		dead = 1;
	for (int i = 0; i < snake_len; i++)
		if (snake_x[i] == nx && snake_y[i] == ny)
			dead = 1;
	if (dead)
		return;

	if (nx == food_x && ny == food_y) {
		memmove(&snake_x[1], &snake_x[0], sizeof(int) * (size_t)snake_len);
		memmove(&snake_y[1], &snake_y[0], sizeof(int) * (size_t)snake_len);
		snake_x[0] = nx;
		snake_y[0] = ny;
		snake_len++;
		score += 10;
		if (score > best)
			best = score;
		food_x = 2 + rand() % (COLS - 4);
		food_y = 2 + rand() % (ROWS - 4);
	} else {
		memmove(&snake_x[1], &snake_x[0], sizeof(int) * (size_t)(snake_len - 1));
		memmove(&snake_y[1], &snake_y[0], sizeof(int) * (size_t)(snake_len - 1));
		snake_x[0] = nx;
		snake_y[0] = ny;
	}
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int tick = 0;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	reset();
	draw(&fb);

	for (;;) {
		if (nova_poll(&in, &ev, 40) == 0) {
			if (!dead && ++tick >= 4) {
				tick = 0;
				step();
				draw(&fb);
			}
			continue;
		}
		ptr_x = ev.x;
		ptr_y = ev.y;

		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY) {
			if (ev.key == 1)
				return 0;
			if (ev.key == 103 && dir_y == 0) { dir_x = 0; dir_y = -1; }
			if (ev.key == 108 && dir_y == 0) { dir_x = 0; dir_y = 1; }
			if (ev.key == 105 && dir_x == 0) { dir_x = -1; dir_y = 0; }
			if (ev.key == 106 && dir_x == 0) { dir_x = 1; dir_y = 0; }
			continue;
		}
		if (ev.type == NOVA_DOWN) {
			if (nova_back_hit(ev.x, ev.y))
				return 0;
			if (dead) {
				reset();
				draw(&fb);
			}
		}
	}
}
