#!/bin/sh
# install-x11.sh -- fetch the X11 + Mesa stack onto the data disk.
#
# The image stays small; this pulls ~110 MB of Debian packages at first run and
# unpacks them under /data/x11 (persistent).  Extracting to a prefix keeps the
# initramfs untouched, and Xorg is started with -modulepath/-xkbdir.
set -e

PREFIX=/data/x11
ROOT=$PREFIX/root
LIST=/system/share/x11-packages.txt
MIRROR=http://mirrors.aliyun.com/debian

if [ -f $PREFIX/.installed ] && [ -f $PREFIX/.extra ]; then
	echo "X11 already installed in $PREFIX"
	exit 0
fi
if [ ! -f "$LIST" ]; then
	echo "missing $LIST"
	exit 1
fi

mkdir -p $ROOT $PREFIX/debs
DONE=$PREFIX/done.txt
touch $DONE
if [ ! -f $PREFIX/.installed ]; then
total=$(wc -l < $LIST)
i=0
while read -r name file size; do
	[ -n "$file" ] || continue
	i=$((i + 1))
	if grep -qx "$file" $DONE 2>/dev/null; then
		continue
	fi
	deb=$PREFIX/debs/$(basename "$file")
	printf '[%3d/%3d] %s\n' "$i" "$total" "$name"
	if [ ! -f "$deb" ]; then
		wget -q -U novaos -O "$deb" "$MIRROR/$file" || {
			echo "download failed: $file"
			exit 1
		}
	fi
	busybox dpkg-deb -x "$deb" "$ROOT" || {
		echo "extract failed: $file"
		exit 1
	}
	rm -f "$deb"
	echo "$file" >> $DONE
done < "$LIST"
touch $PREFIX/.installed
fi

EXTRA=/system/share/x11-extra.txt
if [ -f "$EXTRA" ] && [ ! -f $PREFIX/.extra ]; then
	while read -r file; do
		[ -n "$file" ] || continue
		if grep -qx "$file" $DONE 2>/dev/null; then
			continue
		fi
		deb=$PREFIX/debs/$(basename "$file")
		printf '[extra] %s\n' "$(basename "$file")"
		if [ ! -f "$deb" ]; then
			wget -q -U novaos -O "$deb" "$MIRROR/$file" || {
				echo "download failed: $file"
				exit 1
			}
		fi
		busybox dpkg-deb -x "$deb" "$ROOT"
		rm -f "$deb"
		echo "$file" >> $DONE
	done < "$EXTRA"
	touch $PREFIX/.extra
fi
sync

mkdir -p $PREFIX/etc
cat > $PREFIX/etc/xorg.conf <<'EOF'
Section "ServerLayout"
    Identifier "layout"
    Screen 0 "screen"
    InputDevice "kbd"
    InputDevice "mouse"
EndSection

Section "Device"
    Identifier "gpu"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
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
    Option "Device" "/dev/input/event0"
EndSection

Section "InputDevice"
    Identifier "mouse"
    Driver "evdev"
    Option "Device" "/dev/input/event3"
EndSection
EOF

touch $PREFIX/.installed
echo "done: X11 + Mesa installed under $PREFIX"
