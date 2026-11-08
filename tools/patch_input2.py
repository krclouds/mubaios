import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

# --- SDK: remember whether the bound tablet is the virtual one -------------
p = os.path.join(SRC, "nova.h")
s = io.open(p, encoding="utf-8").read()
s = s.replace("int abs_fd, rel_fd, kbd_fd, virt_fd;",
              "int abs_fd, rel_fd, kbd_fd, virt_fd;\n\tint abs_virtual;")
io.open(p, "w", encoding="utf-8").write(s)

p = os.path.join(SRC, "nova.c")
s = io.open(p, encoding="utf-8").read()
s = s.replace("in->abs_fd = in->rel_fd = in->kbd_fd = in->virt_fd = -1;",
              "in->abs_fd = in->rel_fd = in->kbd_fd = in->virt_fd = -1;\n\tin->abs_virtual = 0;")
s = s.replace("""	if (in->abs_fd < 0 && in->virt_fd >= 0) {
		struct input_absinfo ai;

		in->abs_fd = in->virt_fd;""",
              """	if (in->abs_fd < 0 && in->virt_fd >= 0) {
		struct input_absinfo ai;

		in->abs_fd = in->virt_fd;
		in->abs_virtual = 1;""")
io.open(p, "w", encoding="utf-8").write(s)

# --- system_server: wait for a real pointer before settling for the fake one
p = os.path.join(SRC, "system_server.c")
s = io.open(p, encoding="utf-8").read()
s = s.replace("""	for (int attempt = 0; attempt < 30; attempt++) {
		if (nova_input_open(&in) == 0 && (in.abs_fd >= 0 || in.rel_fd >= 0))
			break;
		nova_input_close(&in);
		usleep(100000);
	}""",
              """	{
		int bound = 0;

		/* The USB tablet shows up a few hundred ms after inputd creates its
		 * virtual touchscreen.  Wait for the real one, otherwise the desktop
		 * would listen to the injection device and ignore the mouse. */
		for (int attempt = 0; attempt < 40; attempt++) {
			if (nova_input_open(&in) == 0) {
				if ((in.abs_fd >= 0 && !in.abs_virtual) || in.rel_fd >= 0) {
					bound = 1;
					break;
				}
			}
			nova_input_close(&in);
			usleep(100000);
		}
		if (!bound) {
			nova_input_close(&in);
			nova_input_open(&in);
		}
	}""")
s = s.replace("""	scan_apps();
	fprintf(stderr, "system_server: %d apps, screen %dx%d\\n", app_count, fb.w, fb.h);""",
              """	scan_apps();
	{
		char nm[80] = {0};

		if (in.abs_fd >= 0)
			ioctl(in.abs_fd, EVIOCGNAME(sizeof(nm)), nm);
		fprintf(stderr, "system_server: %d apps, screen %dx%d, pointer=%s\\n",
			app_count, fb.w, fb.h, nm[0] ? nm : "(none)");
	}""")
if "#include <sys/ioctl.h>" not in s:
    s = s.replace("#include <unistd.h>", "#include <sys/ioctl.h>\n#include <unistd.h>")
if "#include <linux/input.h>" not in s:
    s = s.replace("#include <sys/ioctl.h>", "#include <linux/input.h>\n#include <sys/ioctl.h>")
io.open(p, "w", encoding="utf-8").write(s)
print("input binding fixed")
