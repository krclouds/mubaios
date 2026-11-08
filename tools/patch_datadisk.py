import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs, root=None):
    p = os.path.join(root or SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s:
            print("MISS", name, a[:60].replace("\n", "\\n"))
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


# --- module lists ---------------------------------------------------------
for path in (os.path.join(SRC, "init.c"), os.path.join(ROOT, "build.py")):
    s = io.open(path, encoding="utf-8").read()
    if "virtio_blk.ko" not in s:
        s = s.replace('"kernel/drivers/net/virtio_net.ko",',
                      '"kernel/drivers/net/virtio_net.ko",\n'
                      '\t"kernel/drivers/block/virtio_blk.ko",')
    io.open(path, "w", encoding="utf-8").write(s)

# --- mount the data disk in init -----------------------------------------
patch("init.c", [
    ("static void configure_net(void)",
     '''static void setup_data_disk(void)
{
	unsigned char magic[2] = {0};
	int fd = open("/dev/vda", O_RDONLY);

	if (fd < 0) {
		printf("[ INFO ] no data disk, /data stays in RAM\\n");
		return;
	}
	if (pread(fd, magic, 2, 1080) == 2 && magic[0] == 0x53 && magic[1] == 0xef) {
		printf("[  OK  ] found ext4 data disk\\n");
	} else {
		printf("[ INFO ] formatting /dev/vda as ext4\\n");
		close(fd);
		system("/bin/mke2fs -t ext4 -F -q /dev/vda");
		fd = open("/dev/vda", O_RDONLY);
	}
	close(fd);
	if (mount("/dev/vda", "/data", "ext4", 0, "") == 0)
		printf("[  OK  ] mounted /dev/vda on /data\\n");
	else
		printf("[ WARN ] cannot mount /dev/vda on /data\\n");
}

static void configure_net(void)'''),
    ("	usleep(300000);\n	configure_net();",
     "	usleep(300000);\n	configure_net();\n	setup_data_disk();"),
])

# make sure /bin/mke2fs exists
p = os.path.join(ROOT, "build.py")
s = io.open(p, encoding="utf-8").read()
if "mke2fs" not in s:
    s = s.replace("mkdir mknod more mount", "mke2fs mkdir mknod more mount")
io.open(p, "w", encoding="utf-8").write(s)
print("data disk support added")
