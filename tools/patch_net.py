import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

p = os.path.join(ROOT, "build.py")
s = io.open(p, encoding="utf-8").read()
if "virtio_net.ko" not in s:
    s = s.replace('"kernel/drivers/hid/hid-generic.ko",',
                  '"kernel/drivers/hid/hid-generic.ko",\n'
                  '    "kernel/drivers/virtio/virtio.ko",\n'
                  '    "kernel/drivers/virtio/virtio_ring.ko",\n'
                  '    "kernel/drivers/virtio/virtio_pci_legacy_dev.ko",\n'
                  '    "kernel/drivers/virtio/virtio_pci_modern_dev.ko",\n'
                  '    "kernel/drivers/virtio/virtio_pci.ko",\n'
                  '    "kernel/drivers/net/virtio_net.ko",')
io.open(p, "w", encoding="utf-8").write(s)

p = os.path.join(SRC, "init.c")
s = io.open(p, encoding="utf-8").read()
if "configure_net" not in s:
    helper = '''
static void configure_net(void)
{
	if (access("/sys/class/net/eth0", F_OK) != 0) {
		printf("[ INFO ] no network interface\\n");
		return;
	}
	system("/sbin/ifconfig eth0 10.0.2.15 netmask 255.255.255.0 up");
	system("/sbin/route add default gw 10.0.2.2");
	system("echo nameserver 10.0.2.3 > /etc/resolv.conf");
	printf("[  OK  ] network eth0 10.0.2.15\\n");
}
'''
    s = s.replace("static void load_modules(void)", helper + "\nstatic void load_modules(void)")
    s = s.replace("	usleep(300000);", "	usleep(300000);\n	configure_net();", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("networking added")
