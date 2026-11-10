"""Make the 0.2 "what changed" visuals: old vs new font, and a redraw-time chart."""

import os
import re
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
FONTS = os.path.join(ROOT, "cache", "fonts")


def load_old_cjk():
    src = open(os.path.join(ROOT, "src", "font_cjk.h"), encoding="utf-8").read()
    glyphs = {}
    for cp, body in re.findall(r"\{\s*0x([0-9a-fA-F]+)\s*,\s*\{([^}]*)\}\s*\}", src):
        rows = [int(v, 16) for v in re.findall(r"0x([0-9a-fA-F]+)", body)]
        if len(rows) == 16:
            glyphs[int(cp, 16)] = rows
    return glyphs


def load_new_cjk():
    data = open(os.path.join(ROOT, "rootfs", "system", "share", "font.bin"), "rb").read()
    _, _, ac, aw, ah, cc, cw, ch, _ = struct.unpack_from("<IIIIIIIII", data, 8)
    off = 44 + ac * (4 + aw * ah)
    glyphs = {}
    for i in range(cc):
        rec = off + i * (4 + cw * ch)
        cp = struct.unpack_from("<I", data, rec)[0]
        glyphs[cp] = data[rec + 4:rec + 4 + cw * ch]
    return glyphs, cw, ch


TEXT = "设置登录密码"


def render_old(glyphs, scale=4):
    w = 16 * len(TEXT) * scale
    img = Image.new("L", (w, 16 * scale), 0)
    d = ImageDraw.Draw(img)
    for i, ch in enumerate(TEXT):
        rows = glyphs.get(ord(ch))
        if not rows:
            continue
        for y, row in enumerate(rows):
            for x in range(16):
                if row & (0x8000 >> x):
                    d.rectangle([(i * 16 + x) * scale, y * scale,
                                 (i * 16 + x) * scale + scale - 1, y * scale + scale - 1], fill=255)
    return img


def render_new(glyphs, cw, ch, scale=4):
    w = cw * len(TEXT) * scale
    img = Image.new("L", (w, ch * scale), 0)
    for i, c in enumerate(TEXT):
        data = glyphs.get(ord(c))
        if not data:
            continue
        g = Image.frombytes("L", (cw, ch), data).resize((cw * scale, ch * scale), Image.NEAREST)
        img.paste(g, (i * cw * scale, 0))
    return img


def font_compare():
    old = load_old_cjk()
    new, cw, ch = load_new_cjk()
    A1 = render_old(old, 1)
    B1 = render_new(new, cw, ch, 1)
    A4 = render_old(old, 4)
    B4 = render_new(new, cw, ch, 4)

    pad, head, gap = 56, 74, 34
    cell_w = max(A4.width, B4.width) + 40
    W = pad * 2 + cell_w * 2
    H = pad * 2 + head + 40 + 44 + A1.height + gap + 44 + 30 + A4.height
    canvas = Image.new("RGB", (W, H), (10, 11, 20))
    d = ImageDraw.Draw(canvas)
    try:
        f = ImageFont.truetype(os.path.join(FONTS, "NotoSansCJKsc-Regular.otf"), 34)
        fs = ImageFont.truetype(os.path.join(FONTS, "NotoSansCJKsc-Regular.otf"), 26)
    except Exception:
        f = fs = ImageFont.load_default()

    for i, (title, sub) in enumerate([("0.1  点阵字", "8×16，只有黑白两态"), ("0.2  font.bin", "TTF 栅格化，8-bit alpha")]):
        x = pad + i * cell_w
        d.text((x, pad), title, font=f, fill=(240, 242, 250))
        d.text((x, pad + 44), sub, font=fs, fill=(150, 156, 180))

    y1 = pad + head + 34
    d.text((pad, y1), "原始大小", font=fs, fill=(120, 126, 150))
    canvas.paste(Image.merge("RGB", (A1, A1, A1)), (pad, y1 + 44))
    canvas.paste(Image.merge("RGB", (B1, B1, B1)), (pad + cell_w, y1 + 44))

    y2 = y1 + 44 + A1.height + gap + 26
    d.text((pad, y2), "放大 4 倍", font=fs, fill=(120, 126, 150))
    canvas.paste(Image.merge("RGB", (A4, A4, A4)), (pad, y2 + 44))
    canvas.paste(Image.merge("RGB", (B4, B4, B4)), (pad + cell_w, y2 + 44))

    canvas.save(os.path.join(OUT, "up-font.png"))
    print("up-font.png", canvas.size)


def perf_chart():
    W, H = 1600, 900
    img = Image.new("RGB", (W, H), (10, 11, 20))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(os.path.join(FONTS, "NotoSansCJKsc-Regular.otf"), 44)
        big = ImageFont.truetype(os.path.join(FONTS, "NotoSansCJKsc-Regular.otf"), 96)
    except Exception:
        f = big = ImageFont.load_default()

    d.text((110, 84), "整屏重绘耗时", font=f, fill=(150, 156, 180))

    vals = [("0.1", 307, (240, 113, 113)), ("0.2", 33, (139, 92, 255))]
    base_y, max_h, bw = 740, 470, 190

    for i, (label, ms, color) in enumerate(vals):
        hgt = max(6, int(max_h * ms / 307))
        x = 330 + i * 480
        d.rounded_rectangle([x, base_y - hgt, x + bw, base_y], 16, fill=color)
        d.text((x + bw // 2, base_y - hgt - 70), "%d ms" % ms, font=big,
               fill=(245, 246, 255), anchor="mm")
        d.text((x + bw // 2, base_y + 46), label, font=f, fill=(180, 186, 210), anchor="mm")

    img.save(os.path.join(OUT, "up-perf.png"))
    print("up-perf.png", img.size)


if __name__ == "__main__":
    font_compare()
    perf_chart()
    sys.exit(0)
