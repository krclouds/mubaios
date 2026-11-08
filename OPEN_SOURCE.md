# Open Source Statement and Provenance

This document states, in verifiable terms, what mubaiOS is licensed under, where every
file in this repository comes from, and what is *not* included. It is meant to be checked,
not just read: every claim below can be reproduced with the commands in
[§6 Verification](#6-verification).

- Project: **mubaiOS 0.1** (x86-64)
- Repository: <https://github.com/krclouds/mubaios>
- License of first-party code: **MIT** — see [LICENSE](LICENSE)
- License of third-party components: listed per component in [THIRD_PARTY.md](THIRD_PARTY.md)

---

## 1. Declaration

The user-space of mubaiOS — PID 1, the system server, the graphics and input SDK, the
application launcher/store, the bitmap font pipeline, the build and test tooling, and all
20 applications — is written for this project and is released under the MIT license.

The same statement ships inside the system: `/system/share/LICENSE`, `/system/share/OPEN_SOURCE.md`, `/system/share/THIRD_PARTY.md`, and the built-in **开源许可 / licenses** app renders them on screen (`src/licenses.c`).

It is **not** derived from, and does **not** embed, any closed-source component. No
decompiled code, no leaked SDK, no proprietary binaries, no commercial game assets are
included. There is no proprietary SDK required to build or run it.

The only pre-existing code in the produced image is the Linux kernel, the module set and
BusyBox (plus the glibc runtime needed by dynamically linked programs); all three are
open source, are redistributed unmodified, and their licenses and upstream sources are
recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

## 2. What is MIT-licensed (first-party)

| Path | Contents |
| --- | --- |
| `src/*.c`, `src/*.h` | PID 1, `system_server`, `nova` SDK, input daemon, 19 applications, generated font/pinyin tables |
| `build.py`, `build_iso.py` | build orchestration and ISO authoring |
| `run.ps1` | QEMU launcher |
| `rootfs/` (scripts, configs) | init scripts, `install-*.sh`, X11/Wine helpers written for this project |
| `tools/*.py` | font/pinyin generation, cpio writer, QMP/serial harness, promo renderer, QA, publish scripts |
| `docs/` | screenshots taken from a running mubaiOS |
| `README.md`, `APPS.md`, `THIRD_PARTY.md`, `VIDEO_QA.md`, this file | documentation |

Nothing in these paths is copied from another project. Icons are drawn procedurally at
runtime (`nova_squircle`, `app_glyph`); there is no third-party icon set in the repository.

## 3. Third-party components (not MIT)

| Component | Version | License | How it is used | Source |
| --- | --- | --- | --- | --- |
| Linux kernel | 6.1.0-50-amd64 (`6.1.176-1`) | GPL-2.0 | unmodified `bzImage` + 30 modules, redistributed in the image | `linux-image-6.1.0-50-amd64-unsigned_6.1.176-1_amd64.deb`, Debian pool |
| BusyBox | Debian build | GPL-2.0 | unmodified static binary (`/bin/busybox` + applet links) | `busybox-static` .deb, Debian pool |
| glibc runtime | 2.41 | LGPL-2.1 | unmodified shared libraries for dynamically linked programs | `libc6` .deb, Debian pool |
| libgcc | 14.x | GPL-2.0 + GCC runtime exception | unmodified `libgcc_s.so.1` | `libgcc-s1` .deb, Debian pool |
| DejaVu Sans Mono | 2.37 | Bitstream Vera / DejaVu | converted offline into the 8×16 ASCII table | dejavu-fonts.github.io |
| Noto Sans CJK SC | Regular | SIL OFL-1.1 | converted offline into the 16×16 CJK table (2 671 glyphs) | Google Noto |
| Unihan `kMandarin` | Unicode 15 | Unicode License | used offline to generate the pinyin table (397 syllables) | unicode.org |
| Python 3 | 3.12 | PSF | build-time tool | python.org |
| Zig (`zig cc`) | 0.13 | MIT | build-time C compiler | ziglang.org |
| pycdlib | 1.14 | LGPL-2.1 | build-time ISO authoring | pypi |
| QEMU | 9.x | GPL-2.0 | test/run environment only, not redistributed | qemu.org |

Full copyright notices and the exact upstream URLs are in [THIRD_PARTY.md](THIRD_PARTY.md).
Nothing listed here is modified; the GPL/LGPL components are redistributed as published by
Debian, and their complete corresponding source is available from the same Debian release.

## 4. What is explicitly *not* in this repository

- No Minecraft / Minecraft Java Edition code, assets or launcher (removed from the project
  before publication; only a shortcut script existed at some point and it is gone).
- No 迷你世界 / Mini World content of any kind, and no repacked third-party builds.
- No anti-cheat drivers, no proprietary Android/Unity runtime, no closed-source SDKs.
- No downloaded binaries of X11, Mesa, Wine or Debian games: those are fetched *at runtime*
  by user-invoked scripts from Debian mirrors and are not part of the repository or the ISO.

## 5. Distribution notes for the ISO

`out/mubaios-0.1-x86_64.iso` (attached to the `v0.1` release) contains:

- the MIT-licensed first-party user space compiled from this repository,
- the GPL-2.0 Linux kernel and modules, and the GPL-2.0 BusyBox binary,
- LGPL-2.1 glibc runtime libraries and `libgcc_s.so.1`,

and nothing else. Because it redistributes GPL/LGPL binaries, the corresponding source is
offered through the Debian package URLs in [THIRD_PARTY.md](THIRD_PARTY.md); if you need a
copy bundled with the image, open an issue and it will be provided.

## 6. Verification

Run these yourself; each one checks a claim above.

```bash
# 1. everything the image needs is built from this repository
python build.py                 # kernel unpack + C compile + font generation + initramfs
python build_iso.py             # ISO authoring
sha256sum out/mubaios-0.1-x86_64.iso

# 2. the published tree is byte-identical to the local tree
python tools/verify_pushed.py   # compares git blob ids of local files with GitHub's tree

# 3. no third-party source files are hiding in the user space
grep -rIl "Copyright" src/ | head        # only the project's own headers
ls src/*.c | wc -l                        # 24 first-party translation units

# 4. what the image actually contains
python - <<'PY'
import gzip, subprocess
subprocess.run(["ls", "-lh", "out/nova-initramfs.cpio.gz"])
PY
```

Reference values for 0.1 (recorded at release time):

| Item | Value |
| --- | --- |
| ISO sha256 | `03CD3A2037894581E3E19BA8AF6A989A3E3FB522F34A1DDB3E4901FD7B9CCB50` |
| ISO size | 15 316 992 bytes (14.6 MiB) |
| initramfs | 15.7 MiB raw, 6.5 MiB gzip |
| first-party C | 24 files, 5 786 lines |

## 7. Contact

Questions about licensing, or a request for the corresponding source of a redistributed
GPL/LGPL component: open an issue at <https://github.com/krclouds/mubaios/issues>.
