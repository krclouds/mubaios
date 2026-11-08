import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs):
    p = os.path.join(SRC, name)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            print("MISS", name, ":", old.splitlines()[0][:70])
            continue
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)


# softer gloss on the icons
patch("nova.c", [(
    """	nova_round_rect_gradient(fb, x, y, w, h, r, top, bottom);
	nova_round_rect_blend(fb, x + w / 12, y + h / 24, w - w / 6, h / 3,
			      r - r / 3, 0xffffff, 16);""",
    """	nova_round_rect_gradient(fb, x, y, w, h, r, top, bottom);
	nova_round_rect_blend(fb, x + w / 8, y + h / 16, w - w / 4, h / 4,
			      r - r / 2, 0xffffff, 9);""")])

# glyph without a doubled shadow, label keeps a 1 px one
patch("system_server.c", [(
    """	gw = nova_text_width(a->icon, 3);
	nova_text_shadow(fb, x + (ICON - gw) / 2, y + (ICON - 48) / 2, a->icon, NOVA_WHITE, 3);

	nw = nova_text_width(a->name, 2);
	nova_text_shadow(fb, x + (ICON - nw) / 2, y + ICON + 12, a->name, 0xe8eaf6, 2);""",
    """	gw = nova_text_width(a->icon, 3);
	nova_text(fb, x + (ICON - gw) / 2, y + (ICON - 48) / 2, a->icon, NOVA_WHITE, 3);

	nw = nova_text_width(a->name, 2);
	nova_text(fb, x + (ICON - nw) / 2 + 1, y + ICON + 13, a->name, 0x05060c, 2);
	nova_text(fb, x + (ICON - nw) / 2, y + ICON + 12, a->name, 0xe8eaf6, 2);""")])

# thinner, dimmer scrollbar
patch("system_server.c", [(
    """	nova_round_rect(fb, fb->w - 24, ty, 8, h, 4, 0x5a5f7a);""",
    """	nova_round_rect_blend(fb, fb->w - 22, ty, 5, h, 3, 0xdfe3f5, 90);""")])

# settings cards: soft shadow + lighter surface
patch("settings.c", [(
    """	nova_round_rect(fb, 60, y, fb->w - 120, 100, 18, 0x1b2030);""",
    """	nova_shadow(fb, 60, y + 3, fb->w - 120, 100, 18, 10, 70);
	nova_round_rect(fb, 60, y, fb->w - 120, 100, 18, 0x1e2438);""")])

# store cards: same treatment
patch("store.c", [(
    """	nova_round_rect(fb, x, y, cw, ch, 16, 0x1b2030);""",
    """	nova_shadow(fb, x, y + 2, cw, ch, 16, 9, 60);
	nova_round_rect(fb, x, y, cw, ch, 16, 0x1e2438);""")])

print("polish patched")
