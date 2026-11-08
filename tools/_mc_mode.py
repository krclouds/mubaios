import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. system_server: pause rendering while /run/mc_mode exists instead of dying
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

anchor = "	for (;;) {\n\t\tint got = nova_poll"
if anchor not in s:
    # locate the main loop's poll call
    idx = s.index("nova_poll(")
    print(s[max(0, idx - 300):idx + 200])
    raise SystemExit("anchor not found")

pause = '''	for (;;) {
		/* Minecraft owns the framebuffer while /run/mc_mode exists; the
		 * desktop stays alive but stops painting so it cannot fight X. */
		if (access("/run/mc_mode", F_OK) == 0) {
			if (!paused) {
				paused = 1;
			}
			usleep(60000);
			continue;
		}
		if (paused) {
			paused = 0;
			nova_cursor_reset(&fb);
			draw_home(&fb, 640, 400, -1);
		}
		int got = nova_poll'''
s = s.replace("	for (;;) {\n\t\tint got = nova_poll", pause, 1)

# declare the paused flag next to the other statics
marker = "static int shade;"
assert marker in s
s = s.replace(marker, marker + "\nstatic int paused;", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)

# 2. minecraft.sh: signal the desktop instead of killing it
MC = os.path.join(ROOT, "rootfs", "system", "bin", "minecraft.sh")
t = open(MC, encoding="utf-8").read()
t = t.replace('''# hand the framebuffer over: the desktop keeps repainting it otherwise
killall system_server 2>/dev/null
killall inputd 2>/dev/null
sleep 1''', '''# hand the framebuffer over: the desktop keeps repainting it otherwise
mkdir -p /run
touch /run/mc_mode
sleep 1''')
t = t.replace('''# give the console back
killall Xorg 2>/dev/null
sleep 1
rm -f /tmp/.X11-unix/X0 2>/dev/null
/system/bin/system_server >/dev/null 2>&1 &''', '''# give the console back
killall Xorg 2>/dev/null
sleep 1
rm -f /tmp/.X11-unix/X0 2>/dev/null
rm -f /run/mc_mode''')
open(MC, "w", encoding="utf-8", newline="\n").write(t)
print("desktop pauses for minecraft instead of dying")
