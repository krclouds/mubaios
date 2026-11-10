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
    d.text((W // 2, 712), "基于 Linux 内核，从零构建的桌面系统",
           font=font(48, False), fill=(200, 206, 228, int(255 * sa)), anchor="mm")
    d.text((W // 2, 786), "0.1  ·  x86-64  ·  MIT 开源",
           font=font(32, False), fill=(132, 140, 172, int(255 * sa)), anchor="mm")
    return base


def outro_card(t, dur):
    base = BG.copy()
    d = ImageDraw.Draw(base, "RGBA")
    a = ease(min(1.0, t / 0.8))
    d.text((W // 2, 400), "mubaiOS 0.1", font=font(120), fill=(255, 255, 255, int(255 * a)), anchor="mm")
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
    ("title", None, 8),
    ("text", ("它是什么", ["内核用 Linux 6.1，之外的每一层都自己写",
                        "PID 1、系统服务、图形栈、应用 SDK",
                        "界面直接写 /dev/fb0，没有 X11、Qt、GTK",
                        "应用是静态 ELF，放进 /apps 就能跑"], "01 / 概览"), 15),
    ("text", ("分层", ["内核层：驱动、调度、文件系统（Debian 6.1.0-50）",
                     "用户态：init → inputd → system_server → 应用进程",
                     "图形层：nova.c 双缓冲、脏矩形、位图字库",
                     "应用层：19 个应用，同一套 C SDK"], "01 / 概览"), 14),
    ("text", ("启动链", ["SeaBIOS 引导 → bzImage → initramfs",
                       "init 挂载 devtmpfs/proc/sys/tmpfs，读 /etc/modules",
                       "按依赖顺序 insmod，等 fb0 与 input 设备就绪",
                       "拉起 inputd 与 system_server，打印启动完成标记"], "01 / 概览"), 14),
    ("scene", ("mb2-home.png", "桌面", "状态栏 · 搜索 · 停靠栏 · 图标网格", 0.05), 11),
    ("scene", ("det-statusbar.png", "状态栏", "时间、日期、信号、电量，每分钟只重绘这一条", 0.04), 6),
    ("scene", ("det-search.png", "搜索框", "占位控件，样式与系统一致", 0.03), 6),
    ("scene", ("det-dock.png", "停靠栏", "四个常驻入口，半透明胶囊 + 手势条", 0.04), 6),
    ("scene", ("mb-shade.png", "快捷设置", "下拉面板：网络 · 蓝牙 · 亮度 · 通知", 0.05), 11),
    ("scene", ("det-tiles.png", "开关磁贴", "六个磁贴，点一下切换状态", 0.04), 6),
    ("scene", ("mb2-store.png", "应用商店", "14 个应用，一键安装到 /apps", 0.05), 11),
    ("scene", ("det-card.png", "应用卡片", "图标、名称、简介、安装按钮", 0.05), 6),
    ("text", ("应用格式", ["可执行文件：/apps/<id>/<id>",
                        "清单文件：/apps/<id>/manifest",
                        "字段：name / icon / color / order",
                        "装完立刻出现在桌面，无需重启"], "02 / 应用"), 13),
    ("code", ("build.py", 1, 13, "清单与约定"), 12),
    ("text", ("SDK 能力", ["窗口：打开 framebuffer、双缓冲提交",
                        "图形：圆角矩形、渐变、阴影、发光、squircle",
                        "文字：UTF-8 解析，ASCII + 2600 多个汉字",
                        "输入：鼠标、滚轮、键盘、软键盘统一成 NovaEvent"], "02 / 应用"), 13),
    ("code", ("src/nova.h", 20, 15, "头文件即接口"), 12),
    ("text", ("内置应用（一）", ["文件：浏览 /apps 与 /data，点文本直接看",
                        "画板：离屏画布，6 px 圆刷，撤销 / 清空",
                        "终端：BusyBox sh，可直接跑静态 ELF",
                        "设置：语言、分辨率、已安装应用"], "02 / 应用"), 11),
    ("text", ("内置应用（二）", ["时钟 · 计算器 · 日历 · 天气 · 相册 · 钢琴",
                        "便签 · 扫雷 · 2048 · 秒表 · 系统监视 · 指南针",
                        "全部是静态 musl ELF，放进 /apps 就能跑",
                        "商店里 14 个应用，一键安装"], "02 / 应用"), 11),
    ("scene", ("mb-terminal.png", "终端", "BusyBox shell，直接跑 Linux 程序", 0.04), 11),
    ("scene", ("det-term.png", "真实输出", "uname -a、free、ls /apps", 0.05), 7),
    ("text", ("输入链路", ["evdev 读 /dev/input/event*",
                        "inputd 用 uinput 建虚拟触摸屏，供脚本与测试调用",
                        "system_server 分发 MOVE / DOWN / UP / WHEEL / KEY",
                        "应用只关心事件，不关心设备"], "03 / 交互"), 12),
        ("text", ("应用一览（一）", ["时钟 · 计算器 · 日历 · 天气 · 相册", 
                        "钢琴 · 便签 · 扫雷 · 2048 · 秒表", 
                        "系统监视 · 指南针 · 关于：商店里 14 个", 
                        "全部静态 musl ELF，装完立刻出现在桌面"], "02 / 应用"), 16),
    ("text", ("应用一览（二）", ["便签内置拼音输入：397 个音节 + 词组", 
                        "扫雷 10×10、15 颗雷，可插旗", 
                        "2048 方向键合并，分数只在内存里", 
                        "钢琴八键、相册六幅程序化画作"], "02 / 应用"), 16),
                                            ("scene", ("ft-settings.png", "设置", "五项系统设置，原生 C 实现", 0.04), 10),
    ("scene", ("ft-about.png", "开源许可", "系统内置的许可声明，可直接翻阅", 0.04), 8),
    ("scene", ("det-about.png", "许可原文", "MIT 全文随系统装在 /system/share", 0.05), 7),
    ("text", ("性能", ["整屏重绘 307 ms → 33 ms",
                     "时钟刷新 307 ms → 0.9 ms",
                     "悬停：只重画图标那一格",
                     "按键：只刷输入行那一条"], "04 / 性能"), 13),
    ("code", ("src/nova.c", 560, 15, "脏矩形刷新"), 13),
    ("code", ("src/system_server.c", 420, 14, "主循环"), 12),
    ("text", ("为什么自己写界面", ["不引入 X11：省 300 MB 依赖和一层进程间通信",
                             "不引入 GUI 框架：整屏重绘 33 ms 已经够快",
                             "字库从 TTF 栅格化成 font.bin，运行时 alpha 混合",
                             "代价：没有窗口管理器，应用是全屏的"], "04 / 性能"), 13),
    ("text", ("构建", ["python build.py      生成内核 + initramfs",
                     "python build_iso.py   打包可启动 ISO",
                     "输出：15.2 MiB，BIOS 直接引导",
                     "改一行 C，几十秒就能重新进系统"], "05 / 复现"), 11),
    ("text", ("复现依赖", ["Python 3.9+ / pycdlib",
                        "Zig 0.13（zig cc 交叉编译到 x86_64-linux-musl）",
                        "Debian 内核包与 BusyBox（构建时解包）",
                        "QEMU（运行、截图、自动化测试）"], "05 / 复现"), 11),
    ("text", ("代码规模", ["init 约 470 行，system_server 约 1360 行",
                        "nova.c 约 1060 行，terminal 约 270 行",
                        "全部 C 代码约 5900 行",
                        "没有第三方 GUI 库，没有构建框架"], "05 / 复现"), 11),
    ("text", ("怎么测", ["QMP 注入键盘鼠标事件，screendump 逐帧截图",
                      "QMP 发键盘、滚轮、鼠标事件",
                      "逐屏断言 UI 状态与文字",
                      "每次改动都跑一遍启动 + 关机流程"], "05 / 复现"), 11),
    ("text", ("开源许可", ["自研代码：MIT",
                        "内核与模块：GPL-2.0（Debian 官方包）",
                        "BusyBox：GPL-2.0，glibc 运行时：LGPL-2.1",
                        "字库：DejaVu（Bitstream Vera）+ Noto（OFL-1.1）"], "06 / 开源"), 13),
    ("text", ("第三方清单", ["THIRD_PARTY.md 逐项列出组件、许可证、来源",
                          "内核与模块附 Debian 源码地址",
                          "不含任何商业游戏代码或资源",
                          "X11、Mesa、Wine 都是运行期按需下载，不进仓库"], "06 / 开源"), 13),
    ("text", ("已知限制", ["仅 x86-64 + BIOS/CSM，不支持 UEFI",
                        "无虚拟内存换页，所有进程都是 root",
                        "无 GPU 加速，3D 走软件渲染",
                        "应用装在内存文件系统，重启回到出厂状态"], "06 / 开源"), 10),
    ("text", ("路线图", ["UEFI 启动与 GPT 支持",
                      "权限模型：每个应用独立 UID 与数据目录",
                      "窗口管理：多窗口与最近任务",
                      "包管理：从仓库直接安装 deb"], "06 / 开源"), 11),
    ("text", ("怎么参与", ["源码、构建脚本、文档都在一个仓库里",
                        "提 issue 说清楚复现步骤和串口日志",
                        "改代码请保持无第三方 GUI 依赖",
                        "欢迎补应用：一个 .c 文件 + 一个清单"], "06 / 开源"), 9),
    ("text", ("字体怎么来的", ["构建时用 Pillow 把 TTF 渲染成灰度图集",
                           "ASCII 8×16，汉字 16×16，共 2947 字",
                           "只收录源码里出现过的字，按需重新生成",
                           "运行时读 font.bin，逐像素 alpha 混合"], "03 / 交互"), 13),
    ("text", ("文件系统", ["/       initramfs（内存，只读+tmpfs 覆盖）",
                       "/data   可选 ext4 数据盘，重启保留",
                       "/apps   已安装应用",
                       "/store  商店内置应用的源",
                       "/run    运行期状态：input.fifo"], "01 / 概览"), 12),
    ("text", ("为什么用 initramfs", ["整个系统 7.2 MiB 压缩后在内存里",
                              "没有磁盘也能启动，不依赖分区表",
                              "改代码就是重新打包，不涉及分区与引导修复",
                              "代价：应用安装不持久（有数据盘时除外）"], "01 / 概览"), 11),
    ("text", ("中英双语", ["所有界面文字过一个翻译表",
                        "nova_tr() 在绘制时查表，应用代码零改动",
                        "设置里切换语言，写入 /data/settings.conf",
                        "日期格式也跟着切换"], "03 / 交互"), 12),
    ("text", ("光标与命中测试", ["软件光标：24×24 保存/恢复，只刷两块小矩形",
                            "悬停高亮：只重绘改动的那一格图标",
                            "命中测试：矩形相交，没有额外的布局引擎",
                            "拖动超过 10px 才算滚动，避免误触"], "03 / 交互"), 11),
    ("text", ("怎么调试", ["串口就是控制台，nova.debug=1 打印启动标记与日志",
                        "QMP 发按键和滚轮，screendump 截图",
                        "每次改动都真启动一遍，确认能进桌面",
                        "崩溃看 /data/*.log 与 dmesg"], "05 / 复现"), 12),
    ("text", ("镜像里有什么", ["内核 bzImage + 30 个模块",
                          "BusyBox 与最小 glibc 运行时",
                          "19 个应用 + 商店源 + 字库",
                          "合计 15.2 MiB，ISO 带 ISOLINUX 引导"], "01 / 概览"), 12),
    ("text", ("从哪来的", ["最早是一个能开机的最小系统（TinyLinux）",
                        "后来重写成自带桌面与应用商店的 mubaiOS",
                        "内核之外每一行都是自己写的",
                        "目的：把操作系统课上讲的东西真的跑起来"], "06 / 开源"), 13),
    ("text", ("名字", ["mubaiOS：木白 OS",
                     "版本 0.1，语义化从 0 开始",
                     "所有源码 MIT，第三方组件单独列明",
                     "欢迎 fork，也欢迎提 issue"], "06 / 开源"), 10),
    ("text", ("输入法怎么做的", ["Unihan 的 kMandarin 字段给出拼音",
                            "筛出 GB2312 一级字，按常用度排序",
                            "397 个音节 + 小词组表，前缀匹配",
                            "空格取第一个候选，数字键选后面的"], "03 / 交互"), 12),
    ("text", ("为什么没有窗口管理器", ["全屏应用更简单：一个进程一块屏幕",
                              "进程切回桌面时 system_server 重画即可",
                              "省掉合成器、焦点管理和 IPC",
                              "代价：不能并排显示两个窗口"], "04 / 性能"), 12),
    ("text", ("性能预算", ["整屏重绘 33 ms（约 30 fps）",
                         "局部重绘只刷改动过的那一块",
                         "时钟刷新 0.9 ms，几乎不占 CPU",
                         "目标：桌面操作始终感觉即时"], "04 / 性能"), 12),
    ("outro", None, 8),
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

    out = os.path.join(OUT, "mubaios-promo-10min.mp4")
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
