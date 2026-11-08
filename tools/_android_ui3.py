# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
lines = open(SS, encoding="utf-8").read().split("\n")

GLYPH = r'''
static void tile_glyph(NovaFB *fb, int i, int cx, int cy, uint32_t fg, uint32_t bg)
{
	if (i == 0) {			/* wifi */
		nova_circle(fb, cx, cy + 7, 4, fg);
		nova_line(fb, cx - 7, cy - 2, cx, cy - 8, fg);
		nova_line(fb, cx, cy - 8, cx + 7, cy - 2, fg);
		nova_line(fb, cx - 12, cy - 8, cx, cy - 17, fg);
		nova_line(fb, cx, cy - 17, cx + 12, cy - 8, fg);
	} else if (i == 1) {		/* bluetooth */
		nova_line(fb, cx, cy - 15, cx, cy + 15, fg);
		nova_line(fb, cx, cy - 15, cx + 9, cy - 7, fg);
		nova_line(fb, cx + 9, cy - 7, cx - 8, cy + 6, fg);
		nova_line(fb, cx, cy + 15, cx + 9, cy + 7, fg);
		nova_line(fb, cx + 9, cy + 7, cx - 8, cy - 6, fg);
	} else if (i == 2) {		/* moon */
		nova_circle(fb, cx - 3, cy - 1, 14, fg);
		nova_circle(fb, cx + 7, cy - 6, 12, bg);
	} else if (i == 3) {		/* plane */
		nova_line(fb, cx - 14, cy + 8, cx + 15, cy - 4, fg);
		nova_line(fb, cx - 2, cy - 14, cx + 15, cy - 4, fg);
		nova_line(fb, cx - 9, cy + 1, cx - 2, cy - 14, fg);
	} else if (i == 4) {		/* flashlight */
		nova_round_rect(fb, cx - 6, cy - 4, 12, 20, 4, fg);
		nova_round_rect(fb, cx - 10, cy - 15, 20, 9, 3, fg);
		nova_fill(fb, cx - 14, cy - 19, 3, 14, fg);
		nova_fill(fb, cx + 11, cy - 19, 3, 14, fg);
	} else {			/* rotate */
		for (int k = 0; k < 9; k++) {
			float a = (float)k * 0.7f;
			int px = cx + (int)(13 * cosf(a));
			int py = cy + (int)(13 * sinf(a));

			nova_circle(fb, px, py, 3, fg);
		}
		nova_circle(fb, cx, cy, 5, fg);
	}
}
'''

out = []
for i, ln in enumerate(lines):
    if ln.strip().startswith("static void shade_tile_rect("):
        out.extend(GLYPH.split("\n"))
    if "nova_circle(fb, x + 36, y + 32, 18, tile_on[i] ? 0xa9b6ff : 0x3a4160);" in ln:
        ind = ln[:len(ln) - len(ln.lstrip("\t"))]
        out.append(ind + "nova_circle(fb, x + 40, y + 34, 21, tile_on[i] ? 0xa9b6ff : 0x3a4160);")
        out.append(ind + "tile_glyph(fb, i, x + 40, y + 34, tile_on[i] ? 0x2f3a63 : 0x232a40,")
        out.append(ind + "\t   tile_on[i] ? 0xa9b6ff : 0x3a4160);")
        continue
    if "nova_circle(fb, x + 36, y + 32, 8, tile_on[i] ? 0x2f3a63 : 0x1a2032);" in ln:
        continue
    out.append(ln)
    if "(fb->w - 112) * 68 / 100, 26, 13, 0x6c5ce7);" in ln:
        ind = ln[:len(ln) - len(ln.lstrip("\t"))]
        out.append(ind + "nova_circle(fb, 56 + (fb->w - 112) * 68 / 100, 443, 19, 0xffffff);")

open(SS, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("tile glyphs + knob applied")
