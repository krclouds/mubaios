# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# 1. escapes -> literal characters so genfont can pick the glyphs up
pairs = [
    ("\\u641c\\u7d22\\u5e94\\u7528", "搜索应用"),
    ("\\u65e0\\u7ebf\\u7f51\\u7edc", "无线网络"),
    ("\\u84dd\\u7259", "蓝牙"),
    ("\\u52ff\\u6270\\u6a21\\u5f0f", "勿扰模式"),
    ("\\u98de\\u884c\\u6a21\\u5f0f", "飞行模式"),
    ("\\u624b\\u7535\\u7b52", "手电筒"),
    ("\\u81ea\\u52a8\\u65cb\\u8f6c", "自动旋转"),
    ("\\u5feb\\u6377\\u8bbe\\u7f6e", "快捷设置"),
    ("\\u4eae\\u5ea6", "亮度"),
    ("\\u6ca1\\u6709\\u901a\\u77e5", "没有通知"),
]
for a, b in pairs:
    s = s.replace(a, b)

# 2. shade layout: taller panel, roomier rows, clock on the right
s = s.replace("nova_round_rect_gradient(fb, 0, 0, fb->w, 476, 36, 0x1c2238, 0x111527);",
              "nova_round_rect_gradient(fb, 0, 0, fb->w, 604, 36, 0x1c2238, 0x111527);")
s = s.replace('	nova_text(fb, 56, 72, "NovaOS", NOVA_WHITE, 3);\n'
              '	nova_text(fb, 56, 118, "快捷设置", 0x8f96ad, 2);',
              '	nova_text(fb, 56, 58, "NovaOS", NOVA_WHITE, 3);\n'
              '	nova_text(fb, 56, 104, "快捷设置", 0x8f96ad, 2);\n'
              '	{\n'
              '		char now[8];\n'
              '		int nw;\n'
              '\n'
              '		nova_clock(now);\n'
              '		nw = nova_text_width(now, 3);\n'
              '		nova_text_shadow(fb, fb->w - 56 - nw, 58, now, NOVA_WHITE, 3);\n'
              '	}')

# tiles move up a little, brightness/notification follow
s = s.replace("	*y = 158 + (i / cols) * (96 + gap);", "	*y = 150 + (i / cols) * (96 + gap);")
s = s.replace('	nova_text(fb, 56, 372, "亮度", 0x9aa0b5, 2);\n'
              '	nova_round_rect(fb, 56, 404, fb->w - 112, 26, 13, 0x1a2032);\n'
              '	nova_round_rect(fb, 56, 404, (fb->w - 112) * 68 / 100, 26, 13, 0x6c5ce7);\n'
              '\n'
              '	nova_round_rect(fb, 56, 456, fb->w - 112, 78, 24, 0x232a3e);\n'
              '	nova_circle(fb, 92, 484, 14, 0x3a4160);\n'
              '	nova_text(fb, 118, 466, "没有通知", NOVA_WHITE, 2);\n'
              '	nova_text(fb, 118, 498, "NovaOS 0.1", 0x8f96ad, 2);',
              '	nova_text(fb, 56, 396, "亮度", 0x9aa0b5, 2);\n'
              '	nova_round_rect(fb, 56, 430, fb->w - 112, 26, 13, 0x1a2032);\n'
              '	nova_round_rect(fb, 56, 430, (fb->w - 112) * 68 / 100, 26, 13, 0x6c5ce7);\n'
              '\n'
              '	nova_round_rect(fb, 56, 486, fb->w - 112, 86, 24, 0x232a3e);\n'
              '	nova_circle(fb, 94, 516, 15, 0x3a4160);\n'
              '	nova_text(fb, 124, 496, "没有通知", NOVA_WHITE, 2);\n'
              '	nova_text(fb, 124, 530, "NovaOS 0.1", 0x8f96ad, 2);')

# tile icons: small pictogram disc instead of a plain dot
s = s.replace("		nova_circle(fb, x + 34, y + 34, 16, tile_on[i] ? 0xa9b6ff : 0x3a4160);\n"
              '		nova_text(fb, x + 24, y + 62, labels[i], tile_on[i] ? NOVA_WHITE : 0x9aa0b5, 2);',
              "		nova_circle(fb, x + 36, y + 32, 18, tile_on[i] ? 0xa9b6ff : 0x3a4160);\n"
              "		nova_circle(fb, x + 36, y + 32, 8, tile_on[i] ? 0x2f3a63 : 0x1a2032);\n"
              '		nova_text(fb, x + 24, y + 60, labels[i], tile_on[i] ? NOVA_WHITE : 0x9aa0b5, 2);')

# tap-outside threshold follows the new panel height
s = s.replace("} else if (ev.y > 480) {", "} else if (ev.y > 604) {")

# 3. home: drop the duplicated date, lift the search pill, pull the grid up
s = s.replace('	android_status_bar(fb, clock, date);\n'
              '	draw_search(fb, 170);\n'
              '	nova_text(fb, 60, 78, "欢迎回来", NOVA_WHITE, 3);\n'
              '	nova_text(fb, 60, 78 + 52, date, NOVA_DIM, 2);',
              '	android_status_bar(fb, clock, date);\n'
              '	nova_text(fb, 56, 78, "欢迎回来", NOVA_WHITE, 3);\n'
              '	draw_search(fb, 140);')
s = s.replace("	*y0 = 268;", "	*y0 = 222;")

# 4. icon glyphs sit a little smaller inside the squircle
s = s.replace("	app_glyph(fb, a, x + ICON / 2, y + ICON / 2, ICON, NOVA_WHITE, bottom);",
              "	app_glyph(fb, a, x + ICON / 2, y + ICON / 2, ICON * 82 / 100, NOVA_WHITE, bottom);")

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("layout polish applied")
