"""Rewrite the promo SPEC: shorter scenes, more of them, detail crops + more cards."""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "tools", "make_promo10.py")
s = open(PATH, encoding="utf-8").read()

START = "# (kind, payload, weight)"
END = "def build_timeline():"
i = s.index(START)
j = s.index(END)

SPEC_TEXT = '''# every entry is (kind, payload, seconds) - total is exactly TOTAL seconds
SPEC = [
    ("title", None, 8),
    ("text", ("它是什么", ["内核用 Linux 6.1，之外的每一层都自己写",
                        "PID 1、系统服务、图形栈、应用 SDK",
                        "界面直接写 /dev/fb0，没有 X11、Qt、GTK",
                        "应用是静态 ELF，放进 /apps 就能跑"], "01 / 概览"), 15),
    ("text", ("分层", ["内核层：驱动、调度、文件系统（Debian 6.1.0-50）",
                     "用户态：init → inputd → system_server → 应用进程",
                     "图形层：nova.c 双缓冲、脏矩形、位图字库",
                     "应用层：20 个应用，同一套 C SDK"], "01 / 概览"), 14),
    ("text", ("启动链", ["SeaBIOS 引导 → bzImage → initramfs",
                       "init 挂载 devtmpfs/proc/sys/tmpfs，读 /etc/modules",
                       "按依赖顺序 insmod，等 fb0 与 input 设备就绪",
                       "拉起 inputd 与 system_server，打印 NOVA_BOOT_OK"], "01 / 概览"), 14),
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
    ("code", ("APPS.md", 1, 14, "清单与约定"), 12),
    ("text", ("SDK 能力", ["窗口：打开 framebuffer、双缓冲提交",
                        "图形：圆角矩形、渐变、阴影、发光、squircle",
                        "文字：UTF-8 解析，ASCII + 2700 多个汉字",
                        "输入：鼠标、滚轮、键盘、软键盘统一成 NovaEvent"], "02 / 应用"), 13),
    ("code", ("src/nova.h", 1, 16, "头文件即接口"), 12),
    ("scene", ("mb-files.png", "文件", "浏览目录，打开文本文件", 0.04), 9),
    ("scene", ("mb-paint.png", "画板", "离屏画布 + 6px 圆头笔刷", 0.04), 9),
    ("scene", ("mb-terminal.png", "终端", "BusyBox shell，直接跑 Linux 程序", 0.04), 11),
    ("scene", ("det-term.png", "真实输出", "uname -a、free、ls /apps", 0.05), 7),
    ("text", ("输入链路", ["evdev 读 /dev/input/event*",
                        "inputd 用 uinput 建虚拟触摸屏，供脚本与测试调用",
                        "system_server 分发 MOVE / DOWN / UP / WHEEL / KEY",
                        "应用只关心事件，不关心设备"], "03 / 交互"), 12),
    ("scene", ("app-notes.png", "便签", "拼音输入：397 个音节 + 词组", 0.04), 10),
    ("scene", ("app-calc.png", "计算器", "四则运算", 0.03), 7),
    ("scene", ("app-calendar.png", "日历", "月历视图，今日高亮", 0.03), 7),
    ("scene", ("app-weather.png", "天气", "五日预报（演示数据）", 0.03), 7),
    ("scene", ("app-gallery.png", "相册", "程序化生成的画作", 0.03), 7),
    ("scene", ("app-music.png", "钢琴", "八键，鼠标或键盘弹奏", 0.03), 7),
    ("scene", ("app-snake.png", "贪吃蛇", "方向键控制的经典小游戏", 0.03), 7),
    ("scene", ("app-minesweeper.png", "扫雷", "10×10，15 颗雷", 0.03), 7),
    ("scene", ("app-stopwatch.png", "秒表", "开始 / 暂停 / 重置", 0.03), 6),
    ("scene", ("app-sysmon.png", "系统监视", "负载、内存与运行时间", 0.03), 7),
    ("scene", ("app-compass.png", "指南针", "拖动旋转的表盘", 0.03), 6),
    ("scene", ("ft-settings.png", "设置", "五项系统设置，原生 C 实现", 0.04), 10),
    ("scene", ("ft-about.png", "关于设备", "内核、架构、帧缓冲、内存", 0.04), 8),
    ("scene", ("det-about.png", "硬件信息", "全部读自 /proc 与 framebuffer", 0.05), 7),
    ("text", ("性能", ["整屏重绘 307 ms → 35 ms",
                     "时钟刷新 307 ms → 0.9 ms",
                     "悬停：只重画图标那一格",
                     "按键：只刷输入行那一条"], "04 / 性能"), 13),
    ("code", ("src/nova.c", 560, 15, "脏矩形刷新"), 13),
    ("code", ("src/system_server.c", 420, 14, "主循环"), 12),
    ("text", ("为什么自己写界面", ["不引入 X11：省 300 MB 依赖和一层进程间通信",
                             "不引入 GUI 框架：整屏重绘 35 ms 已经够快",
                             "字库自己生成：一个 8×16 点阵表就够",
                             "代价：没有窗口管理器，应用是全屏的"], "04 / 性能"), 13),
    ("text", ("构建", ["python build.py      生成内核 + initramfs",
                     "python build_iso.py   打包可启动 ISO",
                     "输出：14.6 MiB，BIOS 直接引导",
                     "改一行 C，30 秒内能重新进系统"], "05 / 复现"), 11),
    ("text", ("复现依赖", ["Python 3.9+ / pycdlib",
                        "Zig 0.13（zig cc 交叉编译到 x86_64-linux-musl）",
                        "Debian 内核包与 BusyBox（构建时解包）",
                        "QEMU（运行、截图、自动化测试）"], "05 / 复现"), 11),
    ("text", ("代码规模", ["init 458 行 · system_server 507 行",
                        "nova.c 866 行 · terminal 312 行",
                        "全部 C 代码约 5100 行",
                        "没有第三方 GUI 库，没有构建框架"], "05 / 复现"), 11),
    ("text", ("怎么测", ["串口跑 debug shell，用 input tap 驱动界面",
                      "QMP 发键盘、滚轮、鼠标事件",
                      "screendump 截图逐屏断言",
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
    ("outro", None, 8),
]


'''

s = s[:i] + SPEC_TEXT + s[j:]

BUILD = '''def build_timeline():
    tl = []
    t = 0.0
    for kind, payload, sec in SPEC:
        tl.append((kind, t, float(sec), payload))
        t += sec
    return tl, t


'''
k = s.index("def build_timeline():")
k2 = s.index("def scene_frame(")
s = s[:k] + BUILD + s[k2:]

# detail crops, generated once into out/_det-*.png
CROP_CODE = '''

CROPS = {
    "det-statusbar.png": ("mb2-home.png", (0, 0, 820, 58)),
    "det-search.png": ("mb2-home.png", (56, 138, 1232, 206)),
    "det-dock.png": ("mb2-home.png", (410, 650, 870, 760)),
    "det-tiles.png": ("mb-shade.png", (48, 130, 1232, 372)),
    "det-card.png": ("mb2-store.png", (52, 178, 470, 316)),
    "det-term.png": ("mb-terminal.png", (30, 130, 1250, 430)),
    "det-about.png": ("ft-about.png", (48, 172, 720, 546)),
}


def make_crops():
    for name, (src, box) in CROPS.items():
        dst = os.path.join(OUT, name)
        if os.path.exists(dst):
            continue
        img = Image.open(os.path.join(OUT, src)).convert("RGB").crop(box)
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        img.save(dst)


make_crops()
'''

anchor = "def build_timeline():"
s = s.replace(anchor, CROP_CODE + "\n" + anchor, 1)

# exactly the authored length
s = s.replace("TOTAL = 600.0", "TOTAL = None  # computed from SPEC")

open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("spec rewritten, entries:", s.count('    ("'))
