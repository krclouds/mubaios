/*
 * Gallery -- six procedurally drawn "photos".
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>

#include "nova.h"

static int index;
static const char *titles[6] = {"日落", "群山", "海面", "城市", "圆", "森林"};
static int px = 400, py = 300;

static void art(NovaFB *fb, int i, int x, int y, int w, int h)
{
	switch (i) {
	case 0:
		nova_gradient(fb, x, y, w, h, 0xf39c12, 0x6c3483);
		nova_circle(fb, x + w / 2, y + h * 2 / 3, 70, 0xf7dc6f);
		break;
	case 1:
		nova_gradient(fb, x, y, w, h, 0x85c1e9, 0xd6eaf8);
		for (int k = 0; k < 3; k++) {
			int bx = x + 90 + k * 300, by = y + h - 40;
			for (int r = 0; r < 90; r++)
				nova_fill(fb, bx - r * 2, by - r * 2, r * 4, 2, 0x4a5d6b);
		}
		nova_fill(fb, x, y + h - 40, w, 40, 0x3d5a45);
		break;
	case 2:
		nova_gradient(fb, x, y, w, h, 0x2e86c1, 0x1b4f72);
		for (int r = 0; r < 14; r++)
			nova_fill(fb, x + 40 + (r % 5) * 40, y + 80 + r * 34, w - 80 - (r % 3) * 60, 6, 0x85c1e9);
		break;
	case 3:
		nova_gradient(fb, x, y, w, h, 0x17202a, 0x2c3e50);
		for (int b = 0; b < 12; b++) {
			int bw = 50 + (b * 37) % 60, bh = 120 + (b * 53) % 220;
			nova_fill(fb, x + 30 + b * 90, y + h - bh - 40, bw, bh, 0x1c2833);
			for (int wy = 0; wy < bh - 30; wy += 26)
				for (int wx = 0; wx < bw - 16; wx += 22)
					nova_fill(fb, x + 38 + b * 90 + wx, y + h - bh - 26 + wy, 10, 12, 0xf4d03f);
		}
		break;
	case 4:
		nova_gradient(fb, x, y, w, h, 0x1a0b2e, 0x0b0d14);
		for (int c = 0; c < 9; c++)
			nova_circle(fb, x + 80 + (c * 137) % (w - 160), y + 80 + (c * 211) % (h - 160),
				    30 + (c * 17) % 70, c % 2 ? 0xe74c3c : 0x3498db);
		break;
	default:
		nova_gradient(fb, x, y, w, h, 0x145a32, 0x0b3d20);
		for (int t = 0; t < 60; t++) {
			int tx = x + 20 + (t * 97) % (w - 40);
			nova_fill(fb, tx, y + 60, 8, h - 80, 0x4e342e);
			nova_circle(fb, tx + 4, y + 60, 30 + (t % 3) * 8, 0x2e7d32);
		}
		break;
	}
}

static void draw(NovaFB *fb)
{
	int x = 90, y = 160, w = fb->w - 180, h = fb->h - 310;

	nova_app_header(fb, "相册");
	nova_text(fb, x, 132, titles[index], NOVA_DIM, 2);
	art(fb, index, x, y, w, h);

	nova_round_rect(fb, x, y + h + 20, 120, 64, 16, 0x2a2f40);
	nova_text_center(fb, x + 60, y + h + 36, "<", NOVA_WHITE, 3);
	nova_round_rect(fb, x + w - 120, y + h + 20, 120, 64, 16, 0x2a2f40);
	nova_text_center(fb, x + w - 60, y + h + 36, ">", NOVA_WHITE, 3);

	char buf[32];
	snprintf(buf, sizeof(buf), "%d / 6", index + 1);
	nova_text_center(fb, fb->w / 2, y + h + 40, buf, NOVA_TEXT, 2);
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
		if (ev.x < 220 && ev.y > fb.h - 160)
			index = (index + 5) % 6;
		else if (ev.x > fb.w - 220 && ev.y > fb.h - 160)
			index = (index + 1) % 6;
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
