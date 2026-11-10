"""Render the MBOS 60-second promo video.

Frames are composited with Pillow and piped as raw RGB to ffmpeg.
Audio is a synthesized ambient pad (no third-party samples).
"""

import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
W, H, FPS, DUR = 1920, 1080, 30, 60.0

FFMPEG = r"D:\Python\Python312\Scripts\ffmpeg.exe"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"

ACCENT = (124, 92, 255)
ACCENT2 = (54, 209, 220)


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def cover(path):
    img = Image.open(path).convert("RGB")
    # blurred fill background keeps the whole UI visible (no cropping)
    s = max(W / img.width, H / img.height)
    bg = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    bx = (bg.width - W) // 2
    by = (bg.height - H) // 2
    bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (6, 7, 14)), 0.45)
    s2 = H / img.height
    fg = img.resize((int(img.width * s2 + 0.5), H), Image.LANCZOS)
    out = bg.copy()
    out.paste(fg, ((W - fg.width) // 2, 0))
    return out


def kenburns(img, t, zoom=0.07, dx=0.0, dy=0.0):
    z = 1.0 + zoom * t
    cw, ch = int(W / z), int(H / z)
    cx = (W - cw) // 2 + int(dx * (W - cw) / 2 * math.sin(math.pi * t))
    cy = (H - ch) // 2 + int(dy * (H - ch) / 2 * math.sin(math.pi * t))
    cx = max(0, min(W - cw, cx))
    cy = max(0, min(H - ch, cy))
    return img.crop((cx, cy, cx + cw, cy + ch)).resize((W, H), Image.BICUBIC)


def ease(x):
    return x * x * (3 - 2 * x)


def caption(base, text, alpha, sub=None):
    if alpha <= 0.01:
        return
    d = ImageDraw.Draw(base, "RGBA")
    f = font(46)
    fs = font(30, False)
    tw = d.textlength(text, font=f)
    sw = d.textlength(sub, font=fs) if sub else 0
    bw = int(max(tw, sw) + 96)
    bh = 150 if sub else 96
    x, y = 96, H - bh - 96
    a = int(215 * alpha)
    d.rounded_rectangle([x, y, x + bw, y + bh], 26, fill=(10, 12, 20, a))
    d.rounded_rectangle([x, y, x + 8, y + bh], 4, fill=(*ACCENT, a))
    d.text((x + 46, y + 22), text, font=f, fill=(255, 255, 255, int(255 * alpha)))
    if sub:
        d.text((x + 46, y + 86), sub, font=fs, fill=(170, 178, 205, int(255 * alpha)))


def squircle(size, top, bottom, radius_ratio=0.30):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        k = y / max(1, size - 1)
        gd.line([(0, y), (size, y)], fill=(
            int(top[0] + (bottom[0] - top[0]) * k),
            int(top[1] + (bottom[1] - top[1]) * k),
            int(top[2] + (bottom[2] - top[2]) * k), 255))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1],
                                           int(size * 4 * radius_ratio), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    img.paste(grad, (0, 0), mask)
    gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).ellipse([size * 0.10, -size * 0.55, size * 0.95, size * 0.60],
                                  fill=(255, 255, 255, 26))
    img.alpha_composite(Image.composite(gloss, Image.new("RGBA", (size, size)), mask))
    return img


LOGO = squircle(420, (150, 118, 255), (86, 56, 200))
_d = ImageDraw.Draw(LOGO)
_d.text((210, 210), "M", font=font(230), fill=(255, 255, 255, 255), anchor="mm")
LOGO_BIG = LOGO.resize((720, 720), Image.LANCZOS)


def gradient_bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(18 + 10 * k), int(14 + 6 * k), int(42 - 8 * k)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for (cx, cy, r, col) in [(W * 0.78, H * 0.18, 620, (110, 70, 255, 70)),
                             (W * 0.15, H * 0.88, 560, (40, 180, 220, 55))]:
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    return img.convert("RGB")


BG = gradient_bg()


def title_card(t):
    base = BG.copy()
    a = ease(min(1.0, t / 0.9))
    logo = LOGO_BIG.copy()
    if a < 1:
        logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
    sc = 0.92 + 0.08 * a
    logo = logo.resize((int(300 * sc), int(300 * sc)), Image.LANCZOS)
    base.paste(logo, (W // 2 - logo.width // 2, 150), logo)
    d = ImageDraw.Draw(base, "RGBA")
    ta = ease(max(0.0, min(1.0, (t - 0.35) / 0.8)))
    d.text((W // 2, 610), "MBOS", font=font(150), fill=(255, 255, 255, int(255 * ta)), anchor="mm")
    sa = ease(max(0.0, min(1.0, (t - 0.8) / 0.9)))
    d.text((W // 2, 716), "基于 Linux 内核，从零构建的桌面系统",
           font=font(52, False), fill=(190, 196, 220, int(255 * sa)), anchor="mm")
    d.text((W // 2, 792), "0.1  ·  x86-64  ·  完全开源",
           font=font(34, False), fill=(130, 138, 168, int(255 * sa)), anchor="mm")
    return base


def end_card(t):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.8))
    d.text((W // 2, 430), "MBOS 0.1", font=font(150), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    d.text((W // 2, 570), "Linux 6.1  ·  initramfs  ·  62.8 MiB ISO",
           font=font(46, False), fill=(190, 196, 220, int(255 * a)), anchor="mm")
    d.rounded_rectangle([W // 2 - 300, 660, W // 2 + 300, 760], 50,
                        fill=(*ACCENT, int(180 * a)))
    d.text((W // 2, 710), "开源  ·  可修改  ·  可复现", font=font(42, False),
           fill=(255, 255, 255, int(255 * a * 0.95)), anchor="mm")
    return base


# (image, duration, caption, sub, zoom, dx)
SCENES = [
    ("mb-home.png", 8.0, "自研桌面", "状态栏 · 搜索 · 停靠栏", 0.07, 0.15),
    ("mb-shade.png", 6.5, "下拉快捷设置", "网络 · 蓝牙 · 亮度 · 通知", 0.06, 0.0),
    ("mb-settings.png", 6.0, "系统设置", "原生 C 实现，无 GUI 框架", 0.06, -0.15),
    ("mb-about.png", 5.5, "系统信息", "内核 · 架构 · 帧缓冲 · 内存", 0.05, 0.0),
    ("mb-store.png", 7.5, "应用商店", "15 个应用，一键安装", 0.06, 0.15),
    ("mb-terminal.png", 6.0, "真终端", "BusyBox shell · 直接跑 Linux 程序", 0.06, -0.1),
    ("world6.png", 7.5, "迷你世界", "方块沙盒 · 挖与放 · 创造物品栏", 0.07, 0.15),
    ("ime2-text.png", 6.5, "便签 · 拼音输入", "无外部输入法，内置候选", 0.06, 0.0),
]
TITLE_DUR = 6.0
END_DUR = 5.5


def build_timeline():
    tl = [("title", 0.0, TITLE_DUR, None)]
    t = TITLE_DUR - 0.4
    for name, dur, cap, sub, zoom, dx in SCENES:
        path = os.path.join(OUT, name)
        if not os.path.exists(path):
            print("missing", path)
            continue
        tl.append(("scene", t, dur, (name, cap, sub, zoom, dx)))
        t += dur - 0.4
    tl.append(("end", t, END_DUR, None))
    total = t + END_DUR
    return tl, total


def frame_at(t, tl, imgs):
    active = []
    for kind, start, dur, meta in tl:
        if start <= t < start + dur:
            active.append((kind, start, dur, meta))
    out = None
    for kind, start, dur, meta in active:
        lt = t - start
        if kind == "title":
            f = title_card(lt)
        elif kind == "end":
            f = end_card(lt)
        else:
            name, cap, sub, zoom, dx = meta
            src = kenburns(imgs[name], lt / dur, zoom, dx, 0.0)
            f = src
            fade = 0.9
            alpha = min(1.0, lt / 0.4)
            cap_a = alpha * min(1.0, max(0.0, (dur - lt) / fade + 0.4))
            caption(f, cap, cap_a, sub)
        if out is None:
            out = f.convert("RGB")
            if len(active) > 1:
                out = out.convert("RGBA")
        else:
            out = Image.blend(out.convert("RGB"), f.convert("RGB"), 0.5)
    return out


def make_audio(path, total):
    sr = 44100
    n = int(sr * total)
    t = np.linspace(0, total, n, endpoint=False)
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63),
              (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
    seg = total / len(chords)
    sig = np.zeros(n, dtype=np.float64)
    for i, ch in enumerate(chords):
        m = (t >= i * seg) & (t < (i + 1) * seg)
        env = np.sin(np.pi * (t[m] - i * seg) / seg) ** 1.4
        for k, f in enumerate(ch):
            sig[m] += env * (0.5 / (k + 1)) * np.sin(2 * np.pi * f * t[m])
        sig[m] += env * 0.12 * np.sin(2 * np.pi * (ch[0] * 2) * t[m])
    trem = 1.0 + 0.06 * np.sin(2 * np.pi * 0.18 * t)
    sig *= trem
    fade = int(sr * 2.5)
    sig[:fade] *= np.linspace(0, 1, fade) ** 1.5
    sig[-fade:] *= np.linspace(1, 0, fade) ** 1.2
    sig = sig / max(1e-9, np.max(np.abs(sig))) * 0.30
    stereo = np.stack([sig, np.roll(sig, 220)], axis=1)
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    tl, total = build_timeline()
    print("timeline total %.1fs" % total)
    imgs = {name: cover(os.path.join(OUT, name)) for _, _, _, m in tl if m for name in [m[0]]}
    wav = os.path.join(OUT, "_promo_audio.wav")
    make_audio(wav, total)

    out = os.path.join(OUT, "mbos-promo.mp4")
    if os.path.exists(out):
        os.remove(out)
    cmd = [FFMPEG, "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-strict", "-2",
           "-shortest", "-movflags", "+faststart", out]
    log = open(os.path.join(OUT, "_promo_ffmpeg.log"), "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)

    nframes = int(total * FPS)
    for i in range(nframes):
        f = frame_at(i / FPS, tl, imgs)
        proc.stdin.write(f.tobytes())
        if i % 120 == 0:
            print("frame %d/%d" % (i, nframes), flush=True)
    proc.stdin.close()
    proc.wait()
    log.close()
    err = open(os.path.join(OUT, "_promo_ffmpeg.log"), encoding="utf-8", errors="ignore").read()
    tail = "\n".join([l for l in err.splitlines() if "error" in l.lower()][-6:])
    print("ffmpeg exit", proc.returncode)
    if tail:
        print(tail)
    print("out", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")


if __name__ == "__main__":
    main()
