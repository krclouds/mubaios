"""Patch start-x.sh: use modesetting+virgl when a real DRM GPU is present."""
import os

root = r"C:\Users\feifei\Documents\deepseek-harness\default-workspace\nova"
p = os.path.join(root, "rootfs", "system", "bin", "start-x.sh")
s = open(p, "rb").read().replace(b"\r\n", b"\n").decode("utf-8")

if "DRM_DRIVER" not in s:
    # pick the driver and GL stack after the pointer detection
    s = s.replace(
        'echo "xorg: keyboard=/dev/input/$KB pointer=/dev/input/$MS"',
        '''echo "xorg: keyboard=/dev/input/$KB pointer=/dev/input/$MS"

# A virtio-gpu with virgl lets Mesa talk to the host GPU, which is the whole
# point of booting with -device virtio-vga-gl.  Everything else (bochs) only
# has a linear framebuffer, so X has to render through fbdev.
DRM_DRIVER=""
if [ -e /sys/class/drm/card0/device/uevent ]; then
	DRM_DRIVER=$(sed -n 's/^DRIVER=//p' /sys/class/drm/card0/device/uevent)
fi
if [ "$DRM_DRIVER" = "virtio-pci" ] && [ -e /dev/dri/card0 ]; then
	VIDEO_DRIVER=modesetting
	GPU_MODE=virtio
else
	VIDEO_DRIVER=fbdev
	GPU_MODE=fb
fi
echo "xorg: gpu=$DRM_DRIVER driver=$VIDEO_DRIVER"''')

    # config: either modesetting or fbdev
    s = s.replace(
        '''Section "Device"
    Identifier "gpu"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
    Option "SWcursor" "true"
EndSection''',
        '''Section "Device"
    Identifier "gpu"
    Driver "$VIDEO_DRIVER"
EOF
if [ "$GPU_MODE" = "fb" ]; then
	cat >> $PREFIX/etc/xorg.conf <<EOF
    Option "fbdev" "/dev/fb0"
    Option "SWcursor" "true"
EOF
fi
cat >> $PREFIX/etc/xorg.conf <<EOF
EndSection''')

    # GL environment: virgl when we have one, llvmpipe otherwise
    s = s.replace(
        '''export LIBGL_ALWAYS_SOFTWARE=1
export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe''',
        '''if [ "$GPU_MODE" = "fb" ]; then
	export LIBGL_ALWAYS_SOFTWARE=1
	export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe
fi''')

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("start-x.sh patched:", "DRM_DRIVER" in s, "VIDEO_DRIVER" in s, "GPU_MODE" in s)
