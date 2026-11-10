"""Render the 10-minute mubaiOS promo.

Frames are composited with Pillow and piped as raw RGB to ffmpeg.
No third-party footage, no copyrighted music: the pad is synthesized here.
"""

import math
import os

BAR_H = 140
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
W, H, FPS = 1920, 1080, 24
TOTAL = 600.0

FFMPEG = r"D:\Python\Python312\Scripts\ffmpeg.exe"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"   # only used on the build machine, not shipped
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_MONO = os.path.join(ROOT, "cache", "fonts", "DejaVuSansMono.ttf")

ACCENT = (124, 92, 255)
ACCENT2 = (54, 209, 220)
DIM = (168, 176, 202)


def font(size, bold=True, mono=False):
    if mono:
        return ImageFont.truetype(FONT_MONO, size)
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def cover(path):
    """Letterbox the 1280x800 UI into the title-safe area above the caption bar."""
    img = Image.open(path).convert("RGB")
    cw, chh = W, H - BAR_H
    sc = max(cw / img.width, chh / img.height)
    bg = img.resize((int(img.width * sc + 0.5), int(img.height * sc + 0.5)), Image.LANCZOS)
    bx = (bg.width - cw) // 2
    by = (bg.height - chh) // 2
    bg = bg.crop((bx, by, bx + cw, by + chh)).filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", (cw, chh), (6, 7, 14)), 0.45)
    sc2 = min(cw / img.width, chh / img.height)
    fg = img.resize((max(1, int(img.width * sc2 + 0.5)), max(1, int(img.height * sc2 + 0.5))), Image.LANCZOS)
    out = bg.copy()
    out.paste(fg, ((cw - fg.width) // 2, (chh - fg.height) // 2))
    return out


def kenburns(img, t, zoom=0.06, dx=0.1):
    w, h = img.size
    z = 1.0 + zoom * t
    cw, chh = int(w / z), int(h / z)
    cx = (w - cw) // 2 + int(dx * (w - cw) / 2 * math.sin(math.pi * t))
    cy = (h - chh) // 2
    cx = max(0, min(w - cw, cx))
    return img.crop((cx, cy, cx + cw, cy + chh)).resize((w, h), Image.BILINEAR)


def ease(x):
    return x * x * (3 - 2 * x)


def gradient_bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(16 + 9 * k), int(13 + 6 * k), int(38 - 6 * k)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for (cx, cy, r, col) in [(W * 0.8, H * 0.15, 640, (110, 70, 255, 65)),
                             (W * 0.12, H * 0.9, 580, (40, 180, 220, 50))]:
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    return Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")


BG = gradient_bg()


def squircle(size, top, bottom, rr=0.30):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        k = y / max(1, size - 1)
        gd.line([(0, y), (size, y)], fill=(int(top[0] + (bottom[0] - top[0]) * k),
                                          int(top[1] + (bottom[1] - top[1]) * k),
                                          int(top[2] + (bottom[2] - top[2]) * k), 255))
    mask = Image.new("L", (size * 3, size * 3), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 3 - 1, size * 3 - 1], int(size * 3 * rr), fill=255)
    img.paste(grad, (0, 0), mask.resize((size, size), Image.LANCZOS))
    gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).ellipse([size * 0.08, -size * 0.6, size * 0.96, size * 0.58],
                                  fill=(255, 255, 255, 24))
    img.alpha_composite(gloss)
    return img


LOGO = squircle(420, (150, 118, 255), (86, 56, 200))
ImageDraw.Draw(LOGO).text((210, 208), "m", font=font(250), fill=(255, 255, 255, 255), anchor="mm")


def title_card(t, dur):
    base = BG.copy()
    a = ease(min(1.0, t / 0.9))
    logo = LOGO.resize((300, 300), Image.LANCZOS)
    base.paste(logo, (W // 2 - 150, 170), logo)
    d = ImageDraw.Draw(base, "RGBA")
    ta = ease(max(0.0, min(1.0, (t - 0.4) / 0.9)))
    d.text((W // 2, 610), "mubaiOS", font=font(140), fill=(255, 255, 255, int(255 * ta)), anchor="mm")
    sa = ease(max(0.0, min(1.0, (t - 0.9) / 0.9)))
    d.text((W // 2, 712), "0.2 更新：字体、登录、性能",
           font=font(48, False), fill=(200, 206, 228, int(255 * sa)), anchor="mm")
    d.text((W // 2, 786), "0.2  ·  x86-64  ·  MIT 开源",
           font=font(32, False), fill=(132, 140, 172, int(255 * sa)), anchor="mm")
    return base


def outro_card(t, dur):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.8))
    d.text((W // 2, 400), "mubaiOS 0.2", font=font(120), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    d.text((W // 2, 530), "Linux 6.1 · initramfs · %.1f MiB ISO" % iso_mib(),
           font=font(44, False), fill=DIM + (int(255 * a),), anchor="mm")
    d.rounded_rectangle([W // 2 - 330, 620, W // 2 + 330, 720], 50, fill=(*ACCENT, int(190 * a)))
    d.text((W // 2, 670), "MIT  ·  可修改  ·  可复现", font=font(40, False),
           fill=(255, 255, 255, int(240 * a)), anchor="mm")
    d.text((W // 2, 800), "源码与构建脚本：见仓库 README", font=font(28, False),
           fill=(120, 128, 158, int(200 * a)), anchor="mm")
    return base


def text_card(t, dur, title, lines, kicker=None):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.7))
    y = 250
    if kicker:
        d.text((170, y - 92), kicker, font=font(30, False), fill=(*ACCENT2, int(230 * a)))
    d.text((170, y), title, font=font(86), fill=(255, 255, 255, int(255 * a)))
    y += 150
    for i, line in enumerate(lines):
        la = ease(max(0.0, min(1.0, (t - 0.5 - i * 0.45) / 0.6)))
        if la <= 0.01:
            continue
        d.rounded_rectangle([170, y + 12, 178, y + 52], 4, fill=(*ACCENT, int(235 * la)))
        d.text((206, y), line, font=font(38, False), fill=(212, 218, 238, int(255 * la)))
        y += 84
    return base


def code_card(t, dur, path, first, count, title):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.7))
    d.text((150, 96), title, font=font(58), fill=(255, 255, 255, int(255 * a)))
    d.text((150, 172), path, font=font(28, False, mono=True), fill=(*ACCENT2, int(220 * a)))
    src = open(os.path.join(ROOT, path), encoding="utf-8", errors="ignore").read().splitlines()
    lines = src[first - 1:first - 1 + count]
    f = font(26, mono=True)
    y = 236
    for i, line in enumerate(lines):
        la = ease(max(0.0, min(1.0, (t - 0.4 - i * 0.12) / 0.5)))
        if la <= 0.01:
            continue
        col = (150, 158, 184, int(255 * la))
        s = line.rstrip()
        if s.strip().startswith("/*") or s.strip().startswith("*") or s.strip().startswith("//"):
            col = (110, 150, 130, int(230 * la))
        d.text((156, y), "%3d" % (first + i), font=f, fill=(90, 96, 122, int(200 * la)))
        d.text((240, y), s, font=f, fill=col)
        y += 40
    return base


def scrim(base, height=180, max_alpha=185):
    """Bottom gradient so captions read cleanly over the UI."""
    lay = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(height):
        a = int(max_alpha * (i / height) ** 1.6)
        d.line([(0, i), (W, i)], fill=(4, 5, 10, a))
    base.paste(lay, (0, H - height), lay)


def caption(base, text, alpha, sub=None):
    """Full-width lower third: covers only the dock strip, never app content."""
    if alpha <= 0.01:
        return
    bar_h = BAR_H
    lay = Image.new("RGBA", (W, bar_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(bar_h):
        a = int(238 * (i / bar_h) ** 0.7)
        d.line([(0, i), (W, i)], fill=(6, 7, 12, a))
    base.paste(lay, (0, H - bar_h), lay)

    d = ImageDraw.Draw(base, "RGBA")
    f = font(44)
    fs = font(28, False)
    tw = d.textlength(text, font=f)
    y = H - bar_h + 34
    d.rounded_rectangle([88, y + 2, 96, y + 60], 4, fill=(*ACCENT, int(240 * alpha)))
    d.text((116, y - 6), text, font=f, fill=(255, 255, 255, int(255 * alpha)))
    if sub:
        d.text((116 + tw + 26, y + 12), sub, font=fs, fill=(168, 176, 202, int(240 * alpha)))


def iso_mib():
    p = os.path.join(OUT, "mubaios-0.1-x86_64.iso")
    if os.path.exists(p):
        return os.path.getsize(p) / 1024 / 1024
    return 15.2


def iso_size_mib():
    p = os.path.join(OUT, "mubaios-0.1-x86_64.iso")
    if os.path.exists(p):
        return "%.1f MiB" % (os.path.getsize(p) / 1024 / 1024)
    return "62 MiB"


# every entry is (kind, payload, seconds) - total is exactly TOTAL seconds
SPEC = [
    ("title", None, 10),
    ("text", ("这一版更新了什么",
              ["字体：换成 TTF 栅格化的 font.bin",
               "登录：开机动画 + 锁屏 + 首次设置密码",
               "性能：整屏重绘 307 ms → 33 ms",
               "许可：开源声明做成系统里的应用",
               "商店：修掉打包 bug，14 个应用可装"],
              "0.2 / 更新"), 20),

    ("text", ("§1 字体：0.1 的问题",
              ["字是构建时转的 8×16 点阵",
               "只有“有/无”两态，没有灰阶",
               "细笔画糊成一坨，放大更明显",
               "汉字一多，整页看起来像方块堆"],
              "01 / 字体"), 20),
    ("scene", ("up-font.png", "同一句话，两种字",
               "上：0.1 点阵；下：0.2 font.bin", 0.0), 18),
    ("text", ("新做法：把字做成文件",
              ["构建时用 Pillow 读 TTF，4× 超采样",
               "盒式降采样成 8-bit alpha 图集",
               "产物 /system/share/font.bin（779 KB）",
               "运行时读表，逐像素 alpha 混合"],
              "01 / 字体"), 20),
    ("scene", ("pw-home.png", "桌面实拍",
               "同一套排版，字的边缘变柔和了", 0.03), 16),
    ("text", ("字体：数据",
              ["ASCII 8×16，汉字 16×16",
               "共 2947 个汉字，按源码里出现过的字生成",
               "文件缺失自动回退旧点阵，不会黑屏",
               "缩放到 2×/3× 时仍是渐变边缘"],
              "01 / 字体"), 18),

    ("text", ("§2 登录：0.1 没有门槛",
              ["0.1 开机直接进桌面",
               "没有账户概念，也没有锁屏",
               "任何人都能直接操作这台机器"],
              "02 / 登录"), 18),
    ("scene", ("pw-boot.png", "开机动画",
               "窗口标志 + 转圈 + 进度条，约 0.9 秒", 0.05), 16),
    ("scene", ("pw-login.png", "锁屏",
               "时间、头像、本地账户、密码框、回车/箭头", 0.03), 18),
    ("text", ("首次启动：先设密码",
              ["两个输入框：新密码 / 确认密码",
               "Tab 切换，Enter 下一步",
               "空密码提示“密码不能为空”",
               "两次不一致提示“两次输入不一致”"],
              "02 / 登录"), 20),
    ("text", ("密码怎么存",
              ["只存 FNV-1a 哈希，写 /data/login.pw",
               "没有明文，也没有密码表",
               "写完立刻 fsync + sync，掉电不丢",
               "忘记密码：删掉这个文件就回到设置页"],
              "02 / 登录"), 18),
    ("text", ("输错会怎样",
              ["边框变红，提示“密码错误，请重试”",
               "输入框清空，可以继续输",
               "校验通过才进桌面",
               "设完密码这一次不再二次验证"],
              "02 / 登录"), 16),

    ("text", ("§3 性能：时间花在哪",
              ["0.1 整屏重绘 307 ms",
               "其中 297 ms 是壁纸加辉光",
               "每个像素都调了一次 isqrt 求半径",
               "鼠标一动就整屏重画，越动越积压"],
              "03 / 性能"), 20),
    ("scene", ("up-perf.png", "整屏重绘耗时",
               "307 ms → 33 ms", 0.0), 16),
    ("text", ("四个改动",
              ["辉光改成平方衰减，去掉 isqrt",
               "壁纸只算一次，之后整块 memcpy",
               "连续 MOVE 事件合并，只画最新一帧",
               "滚动只刷图标带，悬停只刷一格"],
              "03 / 性能"), 20),
    ("code", ("src/system_server.c", 1370, 14, "主循环与事件合帧"), 16),
    ("text", ("启动也顺带快了",
              ["网络配置原来要等 5.1 秒",
               "改成后台线程 + 缩短轮询",
               "启动到 system_server：8.5 s → 2.9 s",
               "编译从 -Os 换成 -O2，重绘再降"],
              "03 / 性能"), 18),

    ("text", ("§4 开源声明进系统",
              ["仓库里有 LICENSE，但系统里看不到",
               "0.2 加了一个内置应用：开源许可",
               "两页：声明 / MIT 原文全文",
               "第三方清单单独列，按许可证分组"],
              "04 / 许可"), 20),
    ("scene", ("pw-licenses.png", "新应用：开源许可",
               "本项目 MIT、第三方、不包含什么、源码在哪", 0.04), 18),
    ("text", ("随系统装了什么",
              ["/system/share/LICENSE",
               "/system/share/OPEN_SOURCE.md",
               "/system/share/THIRD_PARTY.md",
               "Tab 翻页，Esc 返回，支持滚动"],
              "04 / 许可"), 16),

    ("text", ("§5 商店：一个打包 bug",
              ["0.1 的 /store/apps 里放错了应用",
               "点“安装”没反应，因为源目录不对",
               "补回打包循环后，14 个应用都能装",
               "装完立刻出现在桌面，无需重启"],
              "05 / 商店"), 20),
    ("scene", ("pw-store.png", "应用商店",
               "14 个应用，一键装到 /apps", 0.04), 18),
    ("text", ("安装做了什么",
              ["把 /store/apps/<id> 拷到 /apps/<id>",
               "读 manifest：名称、图标、配色、排序",
               "桌面下次重绘就会带上新图标",
               "卸载就是删目录，没有注册表"],
              "05 / 商店"), 16),

    ("text", ("§6 顺手修掉的",
              ["版本号、文档里的数字全部重新量过",
               "宣传片里的过时说法逐条删掉",
               "README / APPS.md / OPEN_SOURCE.md 同步",
               "ISO 卷标与文件名统一成 0.2"],
              "06 / 其它"), 18),
    ("scene", ("pw-settings.png", "设置页",
               "五项系统设置，版本号已是 0.2", 0.03), 16),
    ("scene", ("pw-terminal.png", "终端",
               "uname 会显示 mubaiOS 与内核版本", 0.04), 16),
    ("text", ("怎么升级",
              ["换掉 ISO 即可，/data 分区保留",
               "没有 /data 也能启动，回到出厂状态",
               "旧盘可以直接挂回来继续用",
               "0.2 的镜像 15.2 MiB"],
              "06 / 其它"), 18),
    ("outro", None, 10),
]




CROPS = {
    "det-statusbar": ("mb2-home.png", (0, 0, 900, 58)),
    "det-search": ("mb2-home.png", (56, 132, 760, 212)),
    "det-dock": ("mb2-home.png", (380, 648, 1030, 772)),
    "det-tiles": ("mb-shade.png", (90, 148, 1210, 316)),
    "det-card": ("mb2-store.png", (86, 196, 1218, 372)),
    "det-term": ("mb-terminal.png", (56, 176, 1010, 520)),
    "det-about": ("ft-about.png", (60, 176, 880, 520)),
}


def make_crops():
    for name, (src, box) in CROPS.items():
        dst = os.path.join(OUT, name + ".png")
        if os.path.exists(dst):
            continue
        img = Image.open(os.path.join(OUT, src)).convert("RGB").crop(box)
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        img.save(dst)


make_crops()

def build_timeline():
    total = sum(sec for _, _, sec in SPEC)
    scale = (TOTAL or total) / total
    tl = []
    t = 0.0
    for kind, payload, sec in SPEC:
        dur = sec * scale
        tl.append((kind, t, dur, payload))
        t += dur
    return tl, t


def detail_card(t, dur, img, cap, sub):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.6))
    w = int(W * 0.78)
    h = max(1, int(img.height * w / img.width))
    if h > int(H * 0.62):
        h = int(H * 0.62)
        w = max(1, int(img.width * h / img.height))
    x = (W - w) // 2
    y = int(H * 0.42) - h // 2
    shadow = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 40, 40 + w, 40 + h], 22, fill=(0, 0, 0, int(120 * a)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    base.paste(shadow, (x - 40, y - 40), shadow)
    panel = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 20, fill=255)
    panel.putalpha(mask)
    base.paste(panel, (x, y), panel)
    d.rounded_rectangle([x, y, x + w, y + h], 20, outline=(255, 255, 255, int(26 * a)), width=2)
    caption(base, cap, min(1.0, t / 0.35) * min(1.0, max(0.0, (dur - t) / 0.8 + 0.3)), sub)
    return base


def scene_frame(kind, payload, t, dur, imgs):
    if kind == "title":
        return title_card(t, dur)
    if kind == "outro":
        return outro_card(t, dur)
    if kind == "text":
        title, lines, kicker = payload
        return text_card(t, dur, title, lines, kicker)
    if kind == "code":
        return code_card(t, dur, *payload)
    name, cap, sub, zoom = payload
    img = imgs.get(name)
    if img is None:
        return BG.copy()
    if name.startswith("det-"):
        return detail_card(t, dur, img, cap, sub)
    f = Image.new("RGB", (W, H), (8, 9, 16))
    f.paste(kenburns(img, min(1.0, t / dur), zoom, 0.12), (0, 0))
    fade = 0.8
    cap_a = min(1.0, t / 0.35) * min(1.0, max(0.0, (dur - t) / fade + 0.3))
    caption(f, cap, cap_a, sub)
    return f


def make_audio(path, total):
    sr = 44100
    n = int(sr * total)
    t = np.linspace(0, total, n, endpoint=False)
    prog = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63),
            (261.63, 329.63, 392.0), (196.0, 246.94, 293.66),
            (220.0, 277.18, 329.63), (146.83, 220.0, 293.66)]
    seg = total / len(prog)
    sig = np.zeros(n, dtype=np.float64)
    for i, ch in enumerate(prog):
        m = (t >= i * seg) & (t < (i + 1) * seg)
        env = np.sin(np.pi * (t[m] - i * seg) / seg) ** 1.2
        for k, f in enumerate(ch):
            sig[m] += env * (0.55 / (k + 1)) * np.sin(2 * np.pi * f * t[m])
        sig[m] += env * 0.10 * np.sin(2 * np.pi * (ch[0] * 3) * t[m])
    sig *= 1.0 + 0.05 * np.sin(2 * np.pi * 0.12 * t)
    fade = int(sr * 3.0)
    sig[:fade] *= np.linspace(0, 1, fade) ** 1.5
    sig[-fade:] *= np.linspace(1, 0, fade) ** 1.2
    sig = sig / max(1e-9, np.max(np.abs(sig))) * 0.28
    stereo = np.stack([sig, np.roll(sig, 300)], axis=1)
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    tl, total = build_timeline()
    names = {p[0] for k, _, _, p in tl if k == "scene"}
    imgs = {}
    for n in names:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            if n.startswith("det-"):
                imgs[n] = Image.open(p).convert("RGB")
            else:
                imgs[n] = cover(p)
        else:
            print("missing scene image", n)
    print("total %.1fs, %d frames" % (total, int(total * FPS)), flush=True)

    wav = os.path.join(OUT, "_promo10_audio.wav")
    make_audio(wav, total)

    out = os.path.join(OUT, "mubaios-0.2-updates.mp4")
    if os.path.exists(out):
        os.remove(out)
    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-strict", "-2", "-shortest",
           "-movflags", "+faststart", out]
    log = open(os.path.join(OUT, "_promo10_ffmpeg.log"), "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)

    nframes = int(total * FPS)
    cached = None
    for i in range(nframes):
        if i % 2 == 1 and cached is not None:
            proc.stdin.write(cached)
            if i % 240 == 0:
                print("frame %d/%d" % (i, nframes), flush=True)
            continue
        t = i / FPS
        frame = None
        for kind, start, dur, payload in tl:
            if start <= t < start + dur:
                frame = scene_frame(kind, payload, t - start, dur, imgs)
                break
        if frame is None:
            frame = BG.copy()
        blob = frame.tobytes()
        cached = blob
        proc.stdin.write(blob)
        if i % 240 == 0:
            print("frame %d/%d" % (i, nframes), flush=True)
    proc.stdin.close()
    proc.wait()
    log.close()
    print("ffmpeg exit", proc.returncode, flush=True)
    print("out", out, os.path.getsize(out) if os.path.exists(out) else "MISSING", flush=True)


if __name__ == "__main__":
    main()
