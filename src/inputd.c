/*
 * inputd -- mubaiOS input service.
 *
 * Creates one persistent virtual touchscreen through /dev/uinput, so the
 * device node exists from early boot and the window manager can open it.
 * Commands arrive on /run/input.fifo:
 *
 *     tap 346 216
 *     swipe 100 600 900 600
 *     key 1
 *
 * Same idea as Android's InputManager (design inspiration only): apps never care where an
 * event came from, they just read evdev like they would on real hardware.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define SCREEN_W 1280
#define SCREEN_H 800
#define FIFO "/run/input.fifo"

static int ufd = -1;

static void emit(int type, int code, int value)
{
	struct input_event ev;

	memset(&ev, 0, sizeof(ev));
	ev.type = type;
	ev.code = code;
	ev.value = value;
	if (write(ufd, &ev, sizeof(ev)) != sizeof(ev))
		perror("uinput write");
}

static void syn(void)
{
	emit(EV_SYN, SYN_REPORT, 0);
}

static int setup_device(void)
{
	struct uinput_setup usetup;
	struct uinput_abs_setup abs;

	ufd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
	if (ufd < 0) {
		perror("/dev/uinput");
		return -1;
	}
	ioctl(ufd, UI_SET_EVBIT, EV_KEY);
	ioctl(ufd, UI_SET_EVBIT, EV_ABS);
	ioctl(ufd, UI_SET_EVBIT, EV_SYN);
	ioctl(ufd, UI_SET_KEYBIT, BTN_TOUCH);
	ioctl(ufd, UI_SET_ABSBIT, ABS_X);
	ioctl(ufd, UI_SET_ABSBIT, ABS_Y);

	memset(&abs, 0, sizeof(abs));
	abs.code = ABS_X;
	abs.absinfo.minimum = 0;
	abs.absinfo.maximum = 32767;
	ioctl(ufd, UI_ABS_SETUP, &abs);
	abs.code = ABS_Y;
	ioctl(ufd, UI_ABS_SETUP, &abs);

	memset(&usetup, 0, sizeof(usetup));
	usetup.id.bustype = BUS_VIRTUAL;
	usetup.id.vendor = 0x4e56;
	usetup.id.product = 0x0001;
	snprintf(usetup.name, UINPUT_MAX_NAME_SIZE, "mubaiOS virtual touchscreen");
	ioctl(ufd, UI_DEV_SETUP, &usetup);
	if (ioctl(ufd, UI_DEV_CREATE) < 0) {
		perror("UI_DEV_CREATE");
		return -1;
	}
	usleep(300000);
	return 0;
}

static int map_x(int x) { return x * 32767 / SCREEN_W; }
static int map_y(int y) { return y * 32767 / SCREEN_H; }

static void move(int x, int y)
{
	emit(EV_ABS, ABS_X, map_x(x));
	emit(EV_ABS, ABS_Y, map_y(y));
}

static void do_tap(int x, int y)
{
	move(x, y);
	emit(EV_KEY, BTN_TOUCH, 1);
	syn();
	usleep(70000);
	emit(EV_KEY, BTN_TOUCH, 0);
	syn();
}

static void do_swipe(int x0, int y0, int x1, int y1)
{
	move(x0, y0);
	emit(EV_KEY, BTN_TOUCH, 1);
	syn();
	for (int i = 1; i <= 14; i++) {
		move(x0 + (x1 - x0) * i / 14, y0 + (y1 - y0) * i / 14);
		syn();
		usleep(18000);
	}
	emit(EV_KEY, BTN_TOUCH, 0);
	syn();
}

static void handle(char *line)
{
	char cmd[32];
	int a, b, c, d;

	if (sscanf(line, "%31s", cmd) != 1)
		return;
	if (strcmp(cmd, "tap") == 0 && sscanf(line, "%*s %d %d", &a, &b) == 2)
		do_tap(a, b);
	else if (strcmp(cmd, "swipe") == 0 && sscanf(line, "%*s %d %d %d %d", &a, &b, &c, &d) == 4)
		do_swipe(a, b, c, d);
	else if (strcmp(cmd, "key") == 0 && sscanf(line, "%*s %d", &a) == 1) {
		emit(EV_KEY, a, 1);
		syn();
		usleep(30000);
		emit(EV_KEY, a, 0);
		syn();
	}
}

int main(void)
{
	signal(SIGPIPE, SIG_IGN);

	if (setup_device() < 0)
		return 1;

	mkfifo(FIFO, 0666);
	for (;;) {
		int fd = open(FIFO, O_RDONLY);
		char buf[256];
		ssize_t n;

		if (fd < 0) {
			usleep(200000);
			continue;
		}
		n = read(fd, buf, sizeof(buf) - 1);
		close(fd);
		if (n <= 0) {
			usleep(100000);
			continue;
		}
		buf[n] = '\0';
		/* a single read may contain several queued commands */
		for (char *line = strtok(buf, "\n"); line; line = strtok(NULL, "\n"))
			handle(line);
	}
	return 0;
}
