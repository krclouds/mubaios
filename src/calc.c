/*
 * Calculator -- four-function calculator for mubaiOS (from the app store).
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "nova.h"

static const char *labels[5][4] = {
	{"7", "8", "9", "/"},
	{"4", "5", "6", "*"},
	{"1", "2", "3", "-"},
	{"0", ".", "=", "+"},
	{"C", "", "", ""},
};

static char expr[64] = "";
static char result[64] = "0";
static int ptr_x = 400, ptr_y = 300;

static void compute(void)
{
	char op = 0;
	char *p = expr;
	double a = strtod(p, &p);
	while (*p == ' ')
		p++;
	if (*p == '+' || *p == '-' || *p == '*' || *p == '/') {
		op = *p++;
		double b = strtod(p, NULL);
		double r = 0;
		switch (op) {
		case '+': r = a + b; break;
		case '-': r = a - b; break;
		case '*': r = a * b; break;
		case '/': r = b != 0 ? a / b : 0; break;
		}
		snprintf(result, sizeof(result), "%g", r);
	} else {
		snprintf(result, sizeof(result), "%g", a);
	}
}

static void draw(NovaFB *fb)
{
	int bw = 260, bh = 100, gap = 20;
	int x0 = (fb->w - (4 * bw + 3 * gap)) / 2;
	int y0 = 230;

	nova_cursor_reset();
	nova_app_header(fb, "计算器");

	nova_round_rect(fb, 60, 150, fb->w - 120, 60, 14, 0x1b2030);
	nova_text(fb, 84, 162, expr[0] ? expr : "输入算式", expr[0] ? NOVA_DIM : 0x4a5068, 2);
	nova_text(fb, fb->w - 84 - nova_text_width(result, 4), 158, result, NOVA_WHITE, 4);

	for (int r = 0; r < 5; r++) {
		for (int c = 0; c < 4; c++) {
			const char *l = labels[r][c];
			if (!l[0])
				continue;
			int x = x0 + c * (bw + gap);
			int y = y0 + r * (bh + gap);
			uint32_t bg = 0x1b2030;

			if (c == 3 && r < 4)
				bg = 0x2a2f40;
			if (strcmp(l, "=") == 0)
				bg = 0x2ecc71;
			if (strcmp(l, "C") == 0)
				bg = 0x3a1620;
			nova_round_rect(fb, x, y, bw, bh, 18, bg);
			nova_text_center(fb, x + bw / 2, y + 26, l,
					 strcmp(l, "=") == 0 ? 0x08130c : NOVA_WHITE, 3);
		}
	}
	nova_cursor_draw(fb, ptr_x, ptr_y);
}

static void press(const char *l)
{
	size_t n = strlen(expr);

	if (strcmp(l, "C") == 0) {
		expr[0] = 0;
		snprintf(result, sizeof(result), "0");
	} else if (strcmp(l, "=") == 0) {
		compute();
	} else if (n < sizeof(expr) - 2) {
		expr[n++] = l[0];
		expr[n] = 0;
	}
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int bw = 260, bh = 100, gap = 20;
	int x0, y0;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	x0 = (fb.w - (4 * bw + 3 * gap)) / 2;
	y0 = 230;
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

		int c = (ev.x - x0) / (bw + gap);
		int r = (ev.y - y0) / (bh + gap);
		if (c >= 0 && c < 4 && r >= 0 && r < 5 && labels[r][c][0] &&
		    nova_hit(ev.x, ev.y, x0 + c * (bw + gap), y0 + r * (bh + gap), bw, bh))
			press(labels[r][c]);
		draw(&fb);
	}
}
