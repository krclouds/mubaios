import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "src", "system_server.c")
s = io.open(P, encoding="utf-8").read()

helper = '''
static int upgrade_pointer(NovaInput *in)
{
	NovaInput probe;

	if (!in->abs_virtual)
		return 0;
	if (nova_input_open(&probe) != 0)
		return 0;
	if (probe.abs_fd >= 0 && !probe.abs_virtual) {
		char nm[80] = {0};

		nova_input_close(in);
		*in = probe;
		ioctl(in->abs_fd, EVIOCGNAME(sizeof(nm)), nm);
		fprintf(stderr, "system_server: pointer switched to %s\\n", nm);
		return 1;
	}
	nova_input_close(&probe);
	return 0;
}
'''
if "upgrade_pointer" not in s:
    s = s.replace("int main(void)\n{", helper + "\nint main(void)\n{", 1)
    s = s.replace('''		if (nova_poll(&in, &ev, 250) == 0) {
			time_t now = time(NULL);''',
                  '''		if (nova_poll(&in, &ev, 250) == 0) {
			time_t now = time(NULL);

			upgrade_pointer(&in);''', 1)
io.open(P, "w", encoding="utf-8").write(s)
print("pointer upgrade added")
