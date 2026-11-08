# mubaiOS 应用手册

> mubaiOS 0.1 · x86-64 · Linux 6.6.142-0-lts（Alpine 内核）+ 自研用户态
> 源码约 5,800 行 C，19 个应用，全部在 `/apps` 下以独立进程运行。

这份文档按「先系统、再交互、再逐个应用、最后改造指南」的顺序写。看完你应该能：
**知道每个应用怎么用、数据存在哪、界面是怎么画出来的、以及怎么自己加一个。**

---


## 7. 源码索引

| 文件 | 行数 | 职责 |
|---|---:|---|
| `src/init.c` | 458 | PID 1：挂载、装模块、起服务、收尸、关机、boot hooks |
| `src/system_server.c` | 507 | 桌面：状态栏、图标网格（含滚动）、导航栏、扫 `/apps`、启动应用 |
| `src/nova.c` | 866 | SDK 实现：framebuffer 双缓冲、绘图、文本、字库、输入、光标、i18n |
| `src/nova.h` | — | SDK 头文件与常量（`NOVA_STATUSBAR_H 44`、`NOVA_NAVBAR_H 72`、主题色） |
| `src/inputd.c` | 170 | 常驻 uinput 触摸屏，读 `/run/input.fifo` |
| `src/input.c` | 39 | `input tap/swipe/key` 命令行工具 |
| `src/world.c` | 608 | 方块沙盒：高度图、体素渲染、贴图、物品栏 |
| `src/terminal.c` | 312 | 终端：shell 子进程、行缓冲、软键盘 |
| `src/notes.c` | 303 | 便签：文本排版 + 拼音输入法 |
| `src/store.c` | 235 | 应用商店：15 个应用的安装 / 打开 / 卸载 |
| `src/game2048.c` | 203 | 2048 |
| `src/settings.c` | 198 | 设置 |
| `src/files.c` | 196 | 文件管理器 |
| `src/paint.c` | 196 | 画板 |
| `src/minesweeper.c` | 170 | 扫雷 |
| `src/snake.c` | 150 | 贪吃蛇 |
| `src/calc.c` | 139 | 计算器 |
| `src/calendar.c` | 120 | 日历 |
| `src/gallery.c` | 120 | 相册 |
| `src/sysmon.c` | 118 | 系统监视 |
| `src/music.c` | 105 | 钢琴（视觉） |
| `src/stopwatch.c` | 104 | 秒表 |
| `src/compass.c` | 100 | 指南针 |
| `src/weather.c` | 93 | 天气（演示） |
| `src/about.c` | 85 | 关于本机 |
| `src/font8x16.h` | 生成 | ASCII 字模 |
| `src/font_cjk.h` | 生成 | 中文字模 |
| `src/pinyin.h` | 生成 | 拼音音节表 |

工具链（`tools/`）：`genfont.py`（TTF → 位图字模）、`genpinyin.py`（Unihan → 拼音表）、
`mkcpio.py`（纯 Python 写 newc cpio）、`qmp.py`（QEMU 控制 + 截图）、`serial.py`（串口交互）、
`ui_test.py`（无头 UI 测试）、`resolve_pkg.py`（Debian 包依赖解析）、`import_deb.py`（deb → 应用）。
