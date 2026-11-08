# 三方组件与许可

mubaiOS 自己的代码（`src/`、`tools/`、`build.py`、`build_iso.py`）以 **MIT** 许可发布，见 `LICENSE`。

镜像里**没有**任何闭源的第三方代码。下面这些是随镜像一起分发的开源二进制（或由脚本在运行时下载），
各自的许可以及源码获取方式列在这里，便于合规再分发。

## 随镜像分发的二进制

| 组件 | 用途 | 许可 | 源码 / 获取方式 |
|---|---|---|---|
| Linux kernel 6.1.0-50-amd64 | 内核 | GPL-2.0 | Debian 源码包 `linux`（`https://packages.debian.org/source/bookworm/linux`），二进制取自 `linux-image-6.1.0-50-amd64-unsigned` |
| 内核模块（bochs、evdev、uinput、ext4、virtio…） | 驱动 | GPL-2.0 | 同上，来自同一个 Debian 内核包 |
| BusyBox 1.35 | `/bin/sh`、`ls`、`cat`、`dpkg-deb` 等 | GPL-2.0 | Debian 源码包 `busybox` |
| glibc 2.41 运行时（`libc.so.6`、`libm.so.6`、`ld-linux-x86-64.so.2`） | 给 .deb 应用用 | LGPL-2.1 | Debian 源码包 `glibc` |
| libgcc_s.so.1 | C++ / Rust 程序运行时 | GPL-2.0 + GCC Runtime Library Exception | Debian 源码包 `gcc-14` |
| DejaVu Sans Mono | 生成 8×16 ASCII 点阵 | Bitstream Vera Fonts License（宽松，可再分发） | `https://dejavu-fonts.github.io/` |
| Noto Sans CJK SC | 生成 16×16 中文字形 | SIL Open Font License 1.1 | `https://github.com/notofonts/noto-cjk` |
| Unihan 读音数据 | 生成拼音表 `src/pinyin.h` | Unicode License | `https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip` |

> 字体点阵（`src/font8x16.h`、`src/font_cjk.h`）是由上面两个**开源**字体在构建时栅格化生成的，
> 不再使用任何 Windows 系统字体。`tools/fetch_fonts.py` 会把字体下载到 `cache/fonts/`。

## 运行时下载、不进入镜像的内容

这些由 shell 脚本在用户机器上从 Debian 镜像站拉取，仓库和 ISO 都不包含：

| 组件 | 脚本 | 许可 |
|---|---|---|
| Xorg、Mesa（llvmpipe/virgl）、X 客户端库 | `rootfs/system/bin/install-x11.sh` | MIT / X11 / LGPL-2.1 等 |
| `xkbcomp`（bookworm 构建） | `rootfs/system/bin/install-x11.sh` | X11 License |
| Wine（`wine64`、`libwine` 及其依赖） | `rootfs/system/bin/install-wine.sh` | LGPL-2.1 |
| Debian 小游戏（bsdgames 等） | `rootfs/system/bin/install-games.sh` | BSD / GPL 等，随包附带的 copyright 文件 |

## 明确不包含的内容

- **Minecraft（我的世界）**：仓库里没有 Mojang 的任何 jar、资源或启动器，系统也没有相关快捷方式。
  以前为了测试曾经在用户机器上临时安装过，已经从镜像和桌面里彻底移除。
- **迷你世界**：从未包含。系统里曾经有一个同名的**自研**方块沙盒 demo（`world.c`），已按要求删除。
- 任何 Windows 系统字体文件本身（只用了开源字体生成点阵）。

## 再分发检查清单

如果你要分发自己构建的 ISO：

1. 保留本文件和 `LICENSE`。
2. 内核、BusyBox 的二进制再分发需要能提供对应源码——上面表格里的 Debian 源码包链接即可满足，
   或者把 `cache/*.deb` 的源码包一起提供。
3. 不要把你自己的 `/data/mc`（Minecraft 资源）打进镜像。
4. 如果你改了字体，确认新字体也是可再分发的许可。
