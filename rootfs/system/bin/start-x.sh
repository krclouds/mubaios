#!/bin/sh
# start-x.sh -- run Xorg on the framebuffer with Mesa's software GL.
#
# Everything lives under /data/x11 (installed by install-x11.sh), so we point
# Xorg at the module/config/xkb directories explicitly and put the libraries on
# LD_LIBRARY_PATH.  GL clients get llvmpipe through LIBGL_DRIVERS_PATH.
#
# The evdev event numbers move between boots (the USB tablet can show up as
# event2 or event3), so the config is generated here from /proc/bus/input/devices
# instead of being baked in at install time.
PREFIX=/data/x11
ROOT=$PREFIX/root
LIB=$ROOT/usr/lib/x86_64-linux-gnu
XORG=$ROOT/usr/lib/xorg/Xorg

if [ ! -x "$XORG" ]; then
	XORG=$ROOT/usr/bin/Xorg
fi
if [ ! -x "$XORG" ]; then
	echo "Xorg not installed; run install-x11.sh first"
	exit 1
fi

# first device whose "Name=" matches $1 -> "eventN"
dev_event() {
	awk -v pat="$1" '
		/^I: / { f = ($0 ~ pat) }
		f && /^H: Handlers=/ {
			for (i = 1; i <= NF; i++)
				if ($i ~ /^event[0-9]+$/) { print $i; exit }
		}' /proc/bus/input/devices
}

# first candidate pattern that resolves to an event node which actually exists
pick() {
	for pat in "$@"; do
		ev=$(dev_event "$pat")
		if [ -n "$ev" ] && [ -e "/dev/input/$ev" ]; then
			echo "$ev"
			return 0
		fi
	done
	return 1
}

KB=$(pick "AT Translated Set 2 keyboard" "[Kk]eyboard") || KB=event0
# Prefer the QEMU tablet (absolute pointer), then the PS/2 mouse.  uinput
# devices (inputd's virtual touchscreen) lose their evdev node when inputd
# exits, so the existence check above keeps us from picking a dead device.
MS=$(pick "QEMU QEMU USB Tablet" "PS/2" "[Mm]ouse") || MS=event1

echo "xorg: keyboard=/dev/input/$KB pointer=/dev/input/$MS"

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
echo "xorg: gpu=$DRM_DRIVER driver=$VIDEO_DRIVER"

mkdir -p $PREFIX/etc
cat > $PREFIX/etc/xorg.conf <<EOF
Section "ServerLayout"
    Identifier "layout"
    Screen 0 "screen"
    InputDevice "kbd"
    InputDevice "mouse"
EndSection

Section "Device"
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
EndSection

Section "Screen"
    Identifier "screen"
    Device "gpu"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1280x800"
    EndSubSection
EndSection

Section "InputDevice"
    Identifier "kbd"
    Driver "evdev"
    Option "Device" "/dev/input/$KB"
EndSection

Section "InputDevice"
    Identifier "mouse"
    Driver "evdev"
    Option "Device" "/dev/input/$MS"
EndSection
EOF

export LD_LIBRARY_PATH=$LIB:$ROOT/usr/lib:$LD_LIBRARY_PATH
export LIBGL_DRIVERS_PATH=$LIB/dri
if [ "$GPU_MODE" = "fb" ]; then
	export LIBGL_ALWAYS_SOFTWARE=1
	export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe
fi
export XKB_CONFIG_ROOT=$ROOT/usr/share/X11/xkb

# Xorg execs /usr/bin/xkbcomp by absolute path; the bundled one is a Debian
# bookworm build (the trixie one segfaults under QEMU's CPU model).
mkdir -p /usr/bin /usr/share /usr/lib
rm -f /usr/bin/xkbcomp
ln -sf /system/bin/xkbcomp /usr/bin/xkbcomp
[ -e /usr/share/X11 ] || ln -sf $ROOT/usr/share/X11 /usr/share/X11
[ -e /usr/lib/xorg ] || ln -sf $ROOT/usr/lib/xorg /usr/lib/xorg
# the default X cursor glyph comes from the "cursor" font in fonts/X11/misc
[ -e /usr/share/fonts ] || ln -sf $ROOT/usr/share/fonts /usr/share/fonts

exec "$XORG" :0 -noreset -nolisten tcp \
	-modulepath "$ROOT/usr/lib/xorg/modules" \
	-configdir "$PREFIX/etc" \
	-xkbdir "$ROOT/usr/share/X11/xkb" \
	-logfile /tmp/xorg.log
