import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# pull the helper block back out of the wrong place
start = s.index("/* Repaint a single icon cell from the cached wallpaper")
end = s.index("static int max_scroll(NovaFB *fb)")
block = s[start:end]
s = s[:start] + s[end:]

# forward declarations so the helper can live right after draw_icon
decl = "static void draw_icon(NovaFB *fb, int x, int y, const struct app *a, int hover);\n"
anchor = "static int shade;\nstatic int paused;"
assert anchor in s
s = s.replace(anchor, anchor + "\nstatic uint32_t *wall_buf;\n" + decl, 1)

# drop the later definition of wall_buf (now declared above)
s = s.replace("static uint32_t *wall_buf;\n\tstatic size_t wall_len", "static size_t wall_len")
s = s.replace("static uint32_t *wall_buf;\n", "", 1) if s.count("static uint32_t *wall_buf;") > 1 else s

# insert the block after draw_icon
idx = s.index("static void draw_nav(NovaFB *fb, int hover_back")
s = s[:idx] + block + s[idx:]

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("helpers moved after draw_icon; wall_buf declared early")
print([l for l in s.splitlines() if "wall_buf" in l][:4])
