"""QA pass for the 10-minute promo: one frame per script entry + contact sheets.

Usage: python tools/qa_promo.py
Outputs out/qa/f_NNN.png and out/qa/sheet_K.png, prints a per-entry report.
"""

import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
QA = os.path.join(OUT, "qa")
FFMPEG = r"D:\Python\Python312\Scripts\ffmpeg.exe"
VIDEO = os.path.join(OUT, "mubaios-promo-10min.mp4")

os.makedirs(QA, exist_ok=True)

# --- load SPEC without running main -----------------------------------------
src = open(os.path.join(ROOT, "tools", "make_promo10.py"), encoding="utf-8").read()
ns = {"__name__": "promo_spec", "__file__": os.path.join(ROOT, "tools", "make_promo10.py")}
exec(compile(src, "make_promo10.py", "exec"), ns)
SPEC = ns["SPEC"]

BANNED = ["NovaOS", "novaos", "MBOS", "mbos", "Android", "android", "迷你", "Minecraft", "我的世界"]

# --- timeline (approximate but monotonic) -----------------------------------
rows = []
tl, total = ns["build_timeline"]()
for idx, (kind, start, dur, payload) in enumerate(tl):
    rows.append((idx, kind, payload, dur, start, start + dur * 0.6))
t = total

total = t + 8.0  # outro tail

report = []
blank = []
for idx, kind, payload, dur, start, mid in rows:
    path = os.path.join(QA, "f_%03d.png" % idx)
    if not os.path.exists(path):
        subprocess.run(
            [FFMPEG, "-y", "-ss", "%.2f" % mid, "-i", VIDEO, "-frames:v", "1", path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if not os.path.exists(path):
        report.append((idx, kind, dur, "NOFRAME"))
        continue
    im = Image.open(path).convert("RGB")
    g = im.convert("L")
    px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    dark = sum(1 for v in px if v < 8) / n
    report.append((idx, kind, dur, "mean=%.1f dark=%.0f%%" % (mean, dark * 100)))
    if mean < 18 and dark > 0.55:
        blank.append(idx)

# --- banned wording ---------------------------------------------------------
bad = []
for idx, kind, payload, dur, start, mid in rows:
    text = payload if isinstance(payload, str) else " ".join(str(x) for x in (payload or []))
    for w in BANNED:
        if w in text:
            bad.append((idx, w, text[:60]))

# --- contact sheets ---------------------------------------------------------
files = [os.path.join(QA, "f_%03d.png" % r[0]) for r in rows if os.path.exists(os.path.join(QA, "f_%03d.png" % r[0]))]
CW, CH = 640, 360
COLS, ROWS = 3, 3
per = COLS * ROWS
sheets = 0
for s in range(0, len(files), per):
    chunk = files[s:s + per]
    sheet = Image.new("RGB", (COLS * CW, ROWS * CH), (10, 10, 14))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(chunk):
        im = Image.open(p).convert("RGB").resize((CW, CH), Image.LANCZOS)
        x, y = (i % COLS) * CW, (i // COLS) * CH
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + CW - 1, y + CH - 1], outline=(60, 60, 80))
        d.text((x + 8, y + 6), os.path.basename(p), fill=(255, 230, 120))
    out = os.path.join(QA, "sheet_%d.png" % (s // per + 1))
    sheet.save(out)
    sheets += 1

print("entries:", len(rows), "approx total: %.1fs" % total, "sheets:", sheets)
print("blank/suspicious frames:", blank if blank else "none")
print("banned wording:", bad if bad else "none")
for r in report:
    print("  %02d %-6s %4ds %s" % (r[0], r[1], r[2], r[3]))
