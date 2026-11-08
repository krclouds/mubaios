/*
 * Stopwatch -- start / stop / reset.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>

#include "nova.h"

static int running;
static double elapsed;
static struct timespec started;
static int px = 400, py = 300;

static double now_s(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec + ts.tv_nsec / 1e9;
}

static void draw(NovaFB *fb)
{
	char buf[64];
	double t = elapsed;

	if (running)
		t += now_s() - (double)started.tv_sec - started.tv_nsec / 1e9;

	int mins = (int)t / 60;
	int secs = (int)t % 60;
	int cs = (int)((t - (int)t) * 100);

	nova_app_header(fb, "秒表");
	snprintf(buf, sizeof(buf), "%02d:%02d.%02d", mins, secs, cs);
	nova_text_center(fb, fb->w / 2, 260, buf, NOVA_WHITE, 10);

	int bx = fb->w / 2 - 320;
	uint32_t c1 = running ? 0xe67e22 : 0x2ecc71;
	nova_round_rect(fb, bx, 520, 200, 84, 20, c1);
	nova_text_center(fb, bx + 100, 540, running ? "暂停" : "开始", 0x08130c, 2);
	nova_round_rect(fb, bx + 240, 520, 200, 84, 20, 0x2a2f40);
	nova_text_center(fb, bx + 340, 540, "重置", NOVA_WHITE, 2);
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
		if (nova_poll(&in, &ev, 60) == 0) {
			if (running) {
				nova_cursor_reset();
				draw(&fb);
				nova_cursor_draw(&fb, px, py);
			}
			continue;
		}
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

		int bx = fb.w / 2 - 320;
		if (nova_hit(ev.x, ev.y, bx, 520, 200, 84)) {
			if (running) {
				elapsed += now_s() - (double)started.tv_sec - started.tv_nsec / 1e9;
				running = 0;
			} else {
				clock_gettime(CLOCK_MONOTONIC, &started);
				running = 1;
			}
		} else if (nova_hit(ev.x, ev.y, bx + 240, 520, 200, 84)) {
			running = 0;
			elapsed = 0;
		}
		nova_cursor_reset();
		draw(&fb);
		nova_cursor_draw(&fb, px, py);
	}
}
