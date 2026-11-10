"""Build /system/share/font.bin from the real TTF files.

Layout (little endian):
    char magic[8]      "NOVAFONT"
    u32  version       1
    u32  ascii_first   32
    u32  ascii_count
    u32  ascii_w, ascii_h          (8, 16)
    u32  cjk_count
    u32  cjk_w, cjk_h              (16, 16)
    ascii table:  ascii_count records of {u32 cp, u8 alpha[w*h]}
    cjk table:    cjk_count   records of {u32 cp, u8 alpha[w*h]}

Glyphs come from DejaVuSansMono (ASCII) and NotoSansCJKsc (CJK) at 4x
supersampling, box-filtered down, so the runtime can alpha-blend them.
"""

import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "cache", "fonts")
OUT = os.path.join(ROOT, "rootfs", "system", "share", "font.bin")

ASCII_TTF = os.path.join(FONTS, "DejaVuSansMono.ttf")
CJK_TTF = os.path.join(FONTS, "NotoSansCJKsc-Regular.otf")

SS = 4                     # supersample factor
AW, AH = 8, 16             # ascii cell
CW, CH = 16, 16            # cjk cell


def render(font_path, size_px, w, h, chars):
    font = ImageFont.truetype(font_path, size_px)
    out = {}
    for ch in chars:
        img = Image.new("L", (w * SS, h * SS), 0)
        d = ImageDraw.Draw(img)
        # draw at baseline-ish offset: centre the glyph cell
        try:
            bbox = d.textbbox((0, 0), ch, font=font)
        except Exception:
            bbox = (0, 0, w * SS, h * SS)
        gw = bbox[2] - bbox[0]
        gh = bbox[3] - bbox[1]
        x = (w * SS - gw) // 2 - bbox[0]
        y = (h * SS - gh) // 2 - bbox[1]
        d.text((x, y), ch, font=font, fill=255)
        small = img.resize((w, h), Image.BOX)
        out[ch] = small.tobytes()
    return out


def main():
    if not os.path.exists(ASCII_TTF) or not os.path.exists(CJK_TTF):
        print("missing ttf in cache/fonts")
        return 1

    ascii_chars = [chr(c) for c in range(32, 127)]
    # ASCII cell is 8x16 -> render at 16 px tall
    ascii_glyphs = render(ASCII_TTF, int(AH * SS * 0.78), AW, AH, ascii_chars)

    cps = []
    try:
        src = open(os.path.join(ROOT, "src", "font_cjk.h"), encoding="utf-8").read()
        import re
        cps = sorted({int(m, 16) for m in re.findall(r"\{\s*0x([0-9a-fA-F]+)\s*,", src)})
    except Exception as exc:
        print("cannot read font_cjk.h:", exc)
        return 1

    cjk_chars = [chr(c) for c in cps]
    cjk_glyphs = render(CJK_TTF, int(CH * SS * 0.86), CW, CH, cjk_chars)

    with open(OUT, "wb") as f:
        f.write(b"NOVAFONT")
        f.write(struct.pack("<IIIIIIIII", 1, 32, len(ascii_chars), AW, AH,
                            len(cjk_chars), CW, CH, 0))
        for ch in ascii_chars:
            f.write(struct.pack("<I", ord(ch)))
            f.write(ascii_glyphs[ch])
        for ch in cjk_chars:
            f.write(struct.pack("<I", ord(ch)))
            f.write(cjk_glyphs[ch])

    print("font.bin", os.path.getsize(OUT), "bytes,", len(ascii_chars), "ascii,", len(cjk_chars), "cjk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
