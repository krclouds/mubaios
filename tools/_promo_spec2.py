"""Add the remaining cards so the film lands near ten minutes without slow scenes."""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "tools", "make_promo10.py")
s = open(PATH, encoding="utf-8").read()

EXTRA = '''    ("text", ("字体怎么来的", ["离线用 Pillow 把 TTF 渲染成点阵",
                           "ASCII 8×16，汉字 16×16，共 2700+ 字",
                           "只收录源码里出现过的字，按需重新生成",
                           "运行时只查一张表，不需要字体引擎"], "03 / 交互"), 13),
    ("text", ("文件系统", ["/       initramfs（内存，只读+tmpfs 覆盖）",
                       "/data   可选 ext4 数据盘，重启保留",
                       "/apps   已安装应用",
                       "/store  商店内置应用的源",
                       "/run    运行期状态：input.fifo、mc_mode"], "01 / 概览"), 12),
    ("text", ("为什么用 initramfs", ["整个系统 5.7 MiB 压缩后塞进内存",
                              "没有磁盘也能启动，开机 1 秒内到桌面",
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
    ("text", ("怎么调试", ["串口就是控制台，nova.debug=1 直接给 shell",
                        "QMP 发按键和滚轮，screendump 截图",
                        "input tap/swipe 用 uinput 模拟触摸",
                        "崩溃看 /data/*.log 与 dmesg"], "05 / 复现"), 12),
    ("text", ("镜像里有什么", ["内核 bzImage + 15 个模块",
                          "BusyBox 与最小 glibc 运行时",
                          "20 个应用 + 商店源 + 字库",
                          "合计 14.6 MiB，ISO 带 ISOLINUX 引导"], "01 / 概览"), 12),
    ("text", ("从哪来的", ["最早是一个能开机的最小系统（TinyLinux）",
                        "后来重写成自带桌面与应用商店的 mubaiOS",
                        "内核之外每一行都是自己写的",
                        "目的：把操作系统课上讲的东西真的跑起来"], "06 / 开源"), 13),
    ("text", ("名字", ["mubaiOS：木白 OS",
                     "版本 0.1，语义化从 0 开始",
                     "所有源码 MIT，第三方组件单独列明",
                     "欢迎 fork，也欢迎提 issue"], "06 / 开源"), 10),
'''

anchor = '    ("outro", None, 8),'
assert anchor in s
s = s.replace(anchor, EXTRA + anchor, 1)

open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("cards added")
