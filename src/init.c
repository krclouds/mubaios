/*
 * mubaiOS init -- PID 1.
 *
 * mubaiOS is a small desktop system built directly on the Linux kernel.
 * PID 1's job is deliberately boring and explicit:
 *
 *   1. mount /proc, /sys, /dev, /tmp, /run
 *   2. insert the kernel modules Nova needs (DRM/bochs framebuffer, evdev,
 *      psmouse, usbhid) with finit_module(2) -- no modprobe, no udev
 *   3. hand the machine to /system/bin/system_server, the graphical shell
 *   4. reap children, restart the shell if it ever dies, power off on request
 */
#define _GNU_SOURCE
#include <dirent.h>
#include <linux/kd.h>

#ifndef KDSETMODE
#define KDSETMODE 0x4B3A
#endif
#ifndef KD_GRAPHICS
#define KD_GRAPHICS 0x1
#endif
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/signalfd.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define VERSION "0.1"

static int console_fd = 1;
static int shutting_down;

/* Modules in dependency order; each is loaded from /lib/modules/<release>/. */


static void say(const char *fmt, ...)
{
	char buf[1024];
	va_list ap;
	int n;

	va_start(ap, fmt);
	n = vsnprintf(buf, sizeof(buf), fmt, ap);
	va_end(ap);
	if (n > 0 && console_fd >= 0)
		(void)!write(console_fd, buf, (size_t)n);
}

static void log_ok(const char *fmt, ...)
{
	char buf[512];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof(buf), fmt, ap);
	va_end(ap);
	say("\033[32m[  OK  ]\033[0m %s\n", buf);
}

static void log_warn(const char *fmt, ...)
{
	char buf[512];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof(buf), fmt, ap);
	va_end(ap);
	say("\033[33m[ WARN ]\033[0m %s\n", buf);
}

static void log_info(const char *fmt, ...)
{
	char buf[512];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof(buf), fmt, ap);
	va_end(ap);
	say("\033[36m[ INFO ]\033[0m %s\n", buf);
}

static int mkdir_p(const char *path, mode_t mode)
{
	char tmp[256];
	char *p;

	if (strlen(path) >= sizeof(tmp))
		return -1;
	strcpy(tmp, path);
	for (p = tmp + 1; *p; p++) {
		if (*p != '/')
			continue;
		*p = '\0';
		if (mkdir(tmp, mode) != 0 && errno != EEXIST)
			return -1;
		*p = '/';
	}
	if (mkdir(tmp, mode) != 0 && errno != EEXIST)
		return -1;
	return 0;
}

static void mount_one(const char *src, const char *target, const char *fstype,
		      unsigned long flags, const char *data)
{
	mkdir_p(target, 0755);
	if (mount(src, target, fstype, flags, data) != 0)
		log_warn("mount %s on %s failed: %s", fstype, target, strerror(errno));
	else
		log_ok("mounted %s", target);
}

static void mount_filesystems(void)
{
	mount_one("devtmpfs", "/dev", "devtmpfs", 0, "mode=0755");
	mount_one("proc", "/proc", "proc", 0, NULL);
	mount_one("sysfs", "/sys", "sysfs", 0, NULL);
	mount_one("devpts", "/dev/pts", "devpts", 0, "mode=0620,gid=5");
	mount_one("tmpfs", "/tmp", "tmpfs", 0, "mode=1777");
	mount_one("tmpfs", "/run", "tmpfs", 0, "mode=0755");
	mount_one("tmpfs", "/data", "tmpfs", 0, "mode=0777");
	mount_one("tmpfs", "/dev/shm", "tmpfs", 0, "mode=1777");
}

static int insmod_file(const char *path)
{
	int fd = open(path, O_RDONLY | O_CLOEXEC);
	int rc;

	if (fd < 0)
		return -errno;
	rc = (int)syscall(SYS_finit_module, fd, "", 0);
	close(fd);
	return rc == 0 ? 0 : -errno;
}


static void setup_data_disk(void)
{
	unsigned char magic[2] = {0};
	int fd = open("/dev/vda", O_RDONLY);

	if (fd < 0) {
		printf("[ INFO ] no data disk, /data stays in RAM\n");
		return;
	}
	if (pread(fd, magic, 2, 1080) == 2 && magic[0] == 0x53 && magic[1] == 0xef) {
		printf("[  OK  ] found ext4 data disk\n");
	} else {
		printf("[ INFO ] formatting /dev/vda as ext4\n");
		close(fd);
		system("/bin/mke2fs -F -q /dev/vda 3900000");
		fd = open("/dev/vda", O_RDONLY);
	}
	close(fd);
	if (mount("/dev/vda", "/data", "ext4", 0, "") == 0)
		printf("[  OK  ] mounted /dev/vda on /data\n");
	else
		printf("[ WARN ] cannot mount /dev/vda on /data\n");
	mkdir("/mnt/host", 0777);
	if (mount("hostshare", "/mnt/host", "9p", 0, "trans=virtio,version=9p2000.L") == 0)
		printf("[  OK  ] host share on /mnt/host\n");
	else
		printf("[ WARN ] no host share\n");
}


static void run_boot_hooks(void)
{
	DIR *d = opendir("/system/boot");
	if (!d)
		return;
	struct dirent *de;
	while ((de = readdir(d)) != NULL) {
		if (de->d_name[0] == '.')
			continue;
		size_t n = strlen(de->d_name);
		if (n < 3 || strcmp(de->d_name + n - 3, ".sh") != 0)
			continue;
		char path[256];
		snprintf(path, sizeof(path), "/system/boot/%s", de->d_name);
		printf("[ INFO ] boot hook %s\n", path);
		fflush(stdout);
		if (fork() == 0) {
			int devnull = open("/dev/null", O_RDWR);

			if (devnull >= 0) {
				dup2(devnull, 0);
				dup2(devnull, 1);
				dup2(devnull, 2);
			}
			execl("/bin/sh", "sh", path, (char *)NULL);
			_exit(127);
		}
		waitpid(-1, NULL, 0);
	}
	closedir(d);
}

static void configure_net(void)
{
	for (int i = 0; i < 50 && access("/sys/class/net/eth0", F_OK) != 0; i++)
		usleep(100000);
	if (access("/sys/class/net/eth0", F_OK) != 0) {
		printf("[ INFO ] no network interface\n");
		return;
	}
	system("/bin/ifconfig eth0 10.0.2.15 netmask 255.255.255.0 up");
	system("/bin/route add default gw 10.0.2.2");
	system("echo nameserver 10.0.2.3 > /etc/resolv.conf");
	printf("[  OK  ] network eth0 10.0.2.15\n");
}

static void load_modules(void)
{
	char kver[128] = {0};
	struct utsname u;
	char line[256];
	FILE *list;

	uname(&u);
	snprintf(kver, sizeof(kver), "%s", u.release);

	/* The build writes /etc/modules in dependency order, so the same init
	 * works for any kernel we ship -- Debian or Alpine. */
	list = fopen("/etc/modules", "r");
	if (!list) {
		log_warn("no /etc/modules: no kernel modules loaded");
		return;
	}
	while (fgets(line, sizeof(line), list)) {
		char path[512];
		size_t len = strlen(line);
		const char *base;

		while (len && (line[len - 1] == '\n' || line[len - 1] == '\r' || line[len - 1] == ' '))
			line[--len] = '\0';
		if (!len || line[0] == '#')
			continue;

		snprintf(path, sizeof(path), "/lib/modules/%s/%s", kver, line);
		int rc = insmod_file(path);
		base = strrchr(line, '/');
		base = base ? base + 1 : line;

		if (rc == 0)
			log_ok("module %s", base);
		else if (rc == -ENOENT)
			log_warn("module missing: %s", base);
		else
			log_warn("module %s failed: %s", base, strerror(-rc));
	}
	fclose(list);
}

static void cmdline_value(const char *key, int *flag)
{
	char buf[1024] = {0};
	int fd = open("/proc/cmdline", O_RDONLY);
	size_t klen = strlen(key);
	ssize_t n;

	if (fd < 0)
		return;
	n = read(fd, buf, sizeof(buf) - 1);
	close(fd);
	if (n <= 0)
		return;
	buf[n] = '\0';
	for (char *p = buf; p && *p; p = strchr(p, ' ')) {
		if (p != buf)
			p++;
		if (strncmp(p, key, klen) == 0 && (p[klen] == '=' || p[klen] == '\0')) {
			*flag = (p[klen] != '=' || p[klen + 1] != '0');
			return;
		}
	}
}

static void probe_graphics(void)
{
	int fd = open("/dev/fb0", O_RDWR);
	struct fb_var_screeninfo vi;
	DIR *dir;
	struct dirent *de;

	if (fd < 0) {
		log_warn("no /dev/fb0 (%s)", strerror(errno));
	} else {
		memset(&vi, 0, sizeof(vi));
		if (ioctl(fd, FBIOGET_VSCREENINFO, &vi) == 0)
			log_ok("framebuffer %ux%u, %u bpp, stride %u",
			       vi.xres, vi.yres, vi.bits_per_pixel, vi.xres_virtual * vi.bits_per_pixel / 8);
		else
			log_warn("FBIOGET_VSCREENINFO failed");
		close(fd);
	}

	dir = opendir("/dev/input");
	if (dir) {
		say("\033[36m[ INFO ]\033[0m input devices:");
		while ((de = readdir(dir)))
			if (de->d_name[0] != '.')
				say(" %s", de->d_name);
		say("\n");
		closedir(dir);
	} else {
		log_warn("no /dev/input");
	}
}

static int cmdline_str(const char *key, char *out, size_t n)
{
	char buf[1024] = {0};
	int fd = open("/proc/cmdline", O_RDONLY);
	size_t klen = strlen(key);
	ssize_t got;

	if (fd < 0)
		return -1;
	got = read(fd, buf, sizeof(buf) - 1);
	close(fd);
	if (got <= 0)
		return -1;
	buf[got] = '\0';
	for (char *p = buf; p && *p; p = strchr(p, ' ')) {
		while (*p == ' ')
			p++;
		if (strncmp(p, key, klen) == 0 && p[klen] == '=') {
			const char *v = p + klen + 1;
			size_t len = strcspn(v, " \n");

			if (len >= n)
				len = n - 1;
			memcpy(out, v, len);
			out[len] = '\0';
			return 0;
		}
	}
	return -1;
}

static void launch_boot_app(void)
{
	char val[64];
	char path[256];

	if (cmdline_str("nova.app", val, sizeof(val)) != 0)
		return;
	snprintf(path, sizeof(path), "/apps/%s/%s", val, val);
	usleep(2000000);
	if (fork() == 0) {
		execl(path, path, (char *)NULL);
		_exit(127);
	}
}

static void spawn_shell(void)
{
	pid_t pid = fork();

	if (pid == 0) {
		int tty = open("/dev/ttyS0", O_RDWR);

		if (tty >= 0) {
			dup2(tty, 0);
			dup2(tty, 1);
			dup2(tty, 2);
			ioctl(tty, TIOCSCTTY, 0);
			if (tty > 2)
				close(tty);
		}
		execl("/bin/sh", "sh", "-i", (char *)NULL);
		_exit(127);
	}
}

static void poweroff_now(void)
{
	say("\n\033[36m[ INFO ]\033[0m mubaiOS shutting down\n");
	shutting_down = 1;
	sync();
	sleep(1);
	reboot(RB_POWER_OFF);
	for (;;)
		pause();
}

int main(void)
{
	sigset_t mask;
	int sfd, shell_mode = 0, debug_mode = 0;
	struct pollfd pfd;
	pid_t child = -1;

	chdir("/");
	umask(022);

	console_fd = open("/dev/console", O_RDWR);
	if (console_fd < 0)
		console_fd = 1;
	else {
		dup2(console_fd, 0);
		dup2(console_fd, 1);
		dup2(console_fd, 2);
	}

	say("\n\033[1;35m");
	say("  _   _                 ___  ____  \n");
	say(" | \\ | | _____   ____ _/ _ \\/ ___| \n");
	say(" |  \\| |/ _ \\ \\ / / _` | | | \\___ \\ \n");
	say(" | |\\  | (_) \\ V / (_| | |_| |___) |\n");
	say(" |_| \\_|\\___/ \\_/ \\__,_|\\___/|____/ \n");
	say("\033[0m\n");
	log_info("mubaiOS %s -- PID 1 starting", VERSION);

	mount_filesystems();
	sethostname("mubaios", 7);
	setenv("PATH", "/system/bin:/bin:/sbin", 1);
	setenv("TZ", "CST-8", 1);
	tzset();
	cmdline_value("nova.shell", &shell_mode);
	cmdline_value("nova.debug", &debug_mode);
	load_modules();
	usleep(300000);
	configure_net();
	setup_data_disk(); /* give psmouse/evdev a moment to create their nodes */
	probe_graphics();
	run_boot_hooks();

	if (!shell_mode) {
		/* inputd owns the virtual touchscreen; start it before the UI */
		mkfifo("/run/input.fifo", 0666);
		if (fork() == 0) {
			sigset_t empty;
			sigemptyset(&empty);
			sigprocmask(SIG_SETMASK, &empty, NULL);
			execl("/system/bin/inputd", "inputd", (char *)NULL);
			_exit(127);
		}
		usleep(250000);
	}

	if (!shell_mode && access("/system/bin/system_server", X_OK) == 0) {
		log_info("starting system_server");
		child = fork();
		if (child == 0) {
			sigset_t empty;

			sigemptyset(&empty);
			sigprocmask(SIG_SETMASK, &empty, NULL);
			execl("/system/bin/system_server", "system_server", (char *)NULL);
			_exit(127);
		}
	} else {
		log_info("no system_server, starting a rescue shell");
		spawn_shell();
	}

	launch_boot_app();
	if (debug_mode)
		spawn_shell();

	say("\nMUBAIOS_BOOT_OK\n\n");

	sigemptyset(&mask);
	sigaddset(&mask, SIGCHLD);
	sigaddset(&mask, SIGTERM);
	sigaddset(&mask, SIGINT);
	sigaddset(&mask, SIGUSR2);
	sigprocmask(SIG_BLOCK, &mask, NULL);

	sfd = signalfd(-1, &mask, SFD_CLOEXEC);
	pfd.fd = sfd;
	pfd.events = POLLIN;

	while (!shutting_down) {
		struct signalfd_siginfo si;
		int r = poll(&pfd, 1, 1000);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (r == 0)
			continue;
		while (read(sfd, &si, sizeof(si)) == (ssize_t)sizeof(si)) {
			switch (si.ssi_signo) {
			case SIGCHLD:
				while (waitpid(-1, NULL, WNOHANG) > 0)
					;
				break;
			case SIGTERM:
			case SIGINT:
			case SIGUSR2:
				poweroff_now();
				break;
			default:
				break;
			}
		}
	}
	return 0;
}
