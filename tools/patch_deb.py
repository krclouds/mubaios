import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "rootfs", "system", "bin", "debinstall.sh")
s = io.open(p, encoding="utf-8").read()
s = s.replace("PKG=$(dpkg-deb -f", "PKG=$(busybox dpkg-deb -f")
s = s.replace("VER=$(dpkg-deb -f", "VER=$(busybox dpkg-deb -f")
s = s.replace("PKG=$(basename", "PKG=$(busybox basename")
s = s.replace("dpkg-deb -x", "busybox dpkg-deb -x")
s = s.replace("BIN=$(find", "BIN=$(busybox find")
s = s.replace("| head -n 1", "| busybox head -n 1")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)

p = os.path.join(ROOT, "build.py")
s = io.open(p, encoding="utf-8").read()
s = s.replace("egrep env expr false free grep",
              "egrep env expr false free grep dpkg dpkg-deb basename find")
io.open(p, "w", encoding="utf-8").write(s)
print("patched debinstall.sh and APPLETS")
