/*
 * input -- send a command to mubaiOS's input service (see inputd.c).
 *
 *   input tap 346 216
 *   input swipe 100 600 900 600
 *   input key 1
 */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	char line[256] = {0};
	int fd, len = 0;

	for (int i = 1; i < argc; i++) {
		int n = snprintf(line + len, sizeof(line) - (size_t)len, "%s%s",
				 i > 1 ? " " : "", argv[i]);
		if (n < 0 || len + n >= (int)sizeof(line))
			break;
		len += n;
	}
	line[len++] = '\n';

	fd = open("/run/input.fifo", O_WRONLY);
	if (fd < 0) {
		perror("/run/input.fifo");
		return 1;
	}
	if (write(fd, line, (size_t)len) != len) {
		perror("write");
		close(fd);
		return 1;
	}
	close(fd);
	return 0;
}
