#!/bin/sh
# debinstall <file.deb> -- unpack a Debian package and register it in /apps.
#
# The image ships a minimal glibc (ld-linux + libc + libm), so command line
# packages that only link against libc can actually run.  GUI packages will
# unpack but cannot start: there is no X11/Wayland here.
set -e

DEB="$1"
if [ -z "$DEB" ] || [ ! -f "$DEB" ]; then
	echo "usage: debinstall <file.deb>"
	exit 1
fi

PKG=$(busybox dpkg-deb -f "$DEB" Package 2>/dev/null || true)
VER=$(busybox dpkg-deb -f "$DEB" Version 2>/dev/null || true)
[ -n "$PKG" ] || PKG=$(busybox basename "$DEB" .deb)
ID=$(echo "$PKG" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9]/_/g')
DEST=/opt/$ID

echo "installing $PKG $VER -> $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"
busybox dpkg-deb -x "$DEB" "$DEST"

BIN=
for cand in "$DEST"/usr/bin/* "$DEST"/bin/* "$DEST"/usr/sbin/*; do
	[ -f "$cand" ] || continue
	case "$cand" in
	*.so*) continue ;;
	esac
	BIN=$cand
	break
done
if [ -z "$BIN" ]; then
	# fall back to the package name inside the tree
	BIN=$(busybox find "$DEST" -type f -perm -u+x 2>/dev/null | busybox head -n 1)
fi
if [ -z "$BIN" ]; then
	echo "no executable found in $PKG"
	exit 2
fi

RUN=${BIN#$DEST}
ICON=$(echo "$PKG" | cut -c1 | tr 'a-z' 'A-Z')

mkdir -p "/apps/$ID"
cat > "/apps/$ID/$ID" <<EOF
#!/bin/sh
exec /lib64/ld-linux-x86-64.so.2 --library-path /lib/x86_64-linux-gnu "$DEST$RUN" "\$@"
EOF
chmod 755 "/apps/$ID/$ID"
cat > "/apps/$ID/manifest" <<EOF
name=$PKG
icon=$ICON
color=8e44ad
order=300
EOF

echo "installed: $BIN"
echo "run: /apps/$ID/$ID"
