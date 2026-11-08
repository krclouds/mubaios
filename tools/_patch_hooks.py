import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "src", "init.c")
s = open(p, encoding="utf-8").read()

if "run_boot_hooks" not in s:
    hook = '''
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
		printf("[ INFO ] boot hook %s\\n", path);
		fflush(stdout);
		if (fork() == 0) {
			execl("/bin/sh", "sh", path, (char *)NULL);
			_exit(127);
		}
		waitpid(-1, NULL, 0);
	}
	closedir(d);
}

'''
    s = s.replace("static void configure_net(void)", hook + "static void configure_net(void)", 1)
    s = s.replace("\tprobe_graphics();\n", "\tprobe_graphics();\n\trun_boot_hooks();\n", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)

print("hooks:", "run_boot_hooks();" in open(p, encoding="utf-8").read())
