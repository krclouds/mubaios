"""Patch init.c so kernel modules come from /etc/modules instead of a fixed table."""
import os

root = r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova"
p = os.path.join(root, "src", "init.c")
s = open(p, encoding="utf-8").read()

start = s.find("static const char *module_list[] = {")
if start >= 0:
    end = s.find("};", start) + 2
    s = s[:start] + s[end:]

old_start = s.find("static void load_modules(void)")
old_end = s.find("\nstatic void cmdline_value", old_start)
new = '''static void load_modules(void)
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

		while (len && (line[len - 1] == '\\n' || line[len - 1] == '\\r' || line[len - 1] == ' '))
			line[--len] = '\\0';
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
'''
s = s[:old_start] + new + s[old_end:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("init.c updated:", "/etc/modules" in s, "module_list" not in s)
