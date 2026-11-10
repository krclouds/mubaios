/*
 * nova.h -- the mubaiOS application SDK.
 *
 * mubaiOS apps are ordinary ELF programs.  They get the screen from /dev/fb0,
 * input from /dev/input/event*, and this small library for drawing.  There is
 * no toolkit behind it: every pixel an app shows is written by these calls.
 */
#ifndef NOVA_H
#define NOVA_H

#include <stddef.h>
#include <stdint.h>

#define NOVA_STATUSBAR_H 44
#define NOVA_NAVBAR_H    72

#define NOVA_BLACK   0x000000
#define NOVA_WHITE   0xffffff
#define NOVA_ACCENT  0x6c5ce7
#define NOVA_TEXT    0xe8e8f0
#define NOVA_DIM     0x9aa0b5
#define NOVA_SURFACE 0x171a26
#define NOVA_CARD    0x232838
#define NOVA_OK      0x2ecc71
#define NOVA_WARN    0xf1c40f
#define NOVA_DANGER  0xe74c3c

typedef struct {
	int fd;
	uint8_t *mem;
	uint32_t *buf;
	size_t len;
	int w, h, bpp, stride;
} NovaFB;

typedef struct {
	int type;   /* NOVA_MOVE / NOVA_DOWN / NOVA_UP / NOVA_KEY / NOVA_WHEEL */
	int x, y;
	int key;
	int value;
} NovaEvent;

enum {
	NOVA_MOVE = 1,
	NOVA_DOWN,
	NOVA_UP,
	NOVA_KEY,
	NOVA_WHEEL,
};

typedef struct {
	int fds[8];
	int nfds;
	int abs_fd, rel_fd, kbd_fd, virt_fd;
	int abs_virtual;
	int has_abs;
	int minx, maxx, miny, maxy;
	int x, y, down;
	int moved;
	int wheel;
	NovaEvent queue[64];
	int qhead, qtail;
} NovaInput;

/* framebuffer */
int  nova_fb_open(NovaFB *fb);
void nova_fb_close(NovaFB *fb);
void nova_flush(NovaFB *fb);
void nova_mark_clean(void);
void nova_flush_rect(NovaFB *fb, int x, int y, int w, int h);
int nova_dirty(void);

/* drawing */
void nova_fill(NovaFB *fb, int x, int y, int w, int h, uint32_t color);
void nova_pixel(NovaFB *fb, int x, int y, uint32_t color);
uint32_t nova_get(NovaFB *fb, int x, int y);
void nova_round_rect(NovaFB *fb, int x, int y, int w, int h, int r, uint32_t color);
void nova_round_rect_gradient(NovaFB *fb, int x, int y, int w, int h, int r,
			       uint32_t top, uint32_t bottom);
void nova_round_outline(NovaFB *fb, int x, int y, int w, int h, int r,
			int thickness, uint32_t color);
void nova_line(NovaFB *fb, int x0, int y0, int x1, int y1, uint32_t color);
void nova_circle(NovaFB *fb, int cx, int cy, int r, uint32_t color);
void nova_gradient(NovaFB *fb, int x, int y, int w, int h,
		   uint32_t top, uint32_t bottom);
void nova_text(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale);
void nova_text_center(NovaFB *fb, int cx, int y, const char *s, uint32_t color, int scale);
void nova_text_shadow(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale);

/* soft / translucent primitives (blend into whatever is already there) */
uint32_t nova_mix(uint32_t a, uint32_t b, int t);
void nova_blend_px(NovaFB *fb, int x, int y, uint32_t c, int alpha);
void nova_glow(NovaFB *fb, int cx, int cy, int r, uint32_t c, int alpha);
void nova_shadow(NovaFB *fb, int x, int y, int w, int h, int r, int blur, int alpha);
void nova_round_rect_blend(NovaFB *fb, int x, int y, int w, int h, int r,
			   uint32_t c, int alpha);
void nova_squircle(NovaFB *fb, int x, int y, int w, int h,
		   uint32_t top, uint32_t bottom);
int  nova_text_width(const char *s, int scale);

/* widgets shared by the system shell and the apps */
void nova_status_bar(NovaFB *fb, const char *left, const char *right);
void nova_back_button(NovaFB *fb, int cx, int cy, int r);
int  nova_hit(int px, int py, int x, int y, int w, int h);
void nova_clock(char *buf, size_t n);
int  nova_lang(void);
void nova_lang_reload(void);
const char *nova_tr(const char *s);
#define L(zh, en) (nova_lang() ? (en) : (zh))
void nova_app_header(NovaFB *fb, const char *title);
int  nova_back_hit(int x, int y);

/* input */
int  nova_input_open(NovaInput *in);
void nova_input_close(NovaInput *in);
int  nova_poll(NovaInput *in, NovaEvent *ev, int timeout_ms);
int  nova_peek(NovaInput *in, NovaEvent *ev);
int  nova_key_ascii(int keycode, int shift);
void nova_set_screen(int w, int h);
void nova_cursor_draw(NovaFB *fb, int x, int y);
void nova_cursor_reset(void);

#endif
