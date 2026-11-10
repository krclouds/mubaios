"""Download the open fonts used by tools/genfont.py.

The build only needs two files:

  cache/fonts/DejaVuSansMono.ttf        Bitstream Vera / DejaVu licence
  cache/fonts/NotoSansCJKsc-Regular.otf SIL Open Font License 1.1

Both are redistributable; see THIRD_PARTY.md. Run this once before
``python build.py`` on a fresh checkout.
"""

import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "cache", "fonts")

FONTS = [
    (
        "DejaVuSansMono.ttf",
        340712,
        [
            "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/"
            "ttf/DejaVuSansMono.ttf",
        ],
    ),
    (
        "NotoSansCJKsc-Regular.otf",
        16437364,
        [
            "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/"
            "NotoSansCJKsc-Regular.otf",
        ],
    ),
]

PROXY = "https://ghfast.top/"


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "mubaios-build"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def main():
    os.makedirs(DEST, exist_ok=True)
    for name, size, urls in FONTS:
        dest = os.path.join(DEST, name)
        if os.path.exists(dest) and os.path.getsize(dest) == size:
            print("ok      ", name, size)
            continue
        ok = False
        for base in urls:
            for url in (base, PROXY + base):
                try:
                    print("fetching", url[:80], "...", flush=True)
                    fetch(url, dest)
                except Exception as exc:  # noqa: BLE001 - try the next mirror
                    print("  failed:", type(exc).__name__, exc)
                    continue
                if os.path.exists(dest) and os.path.getsize(dest) == size:
                    print("saved   ", name, size)
                    ok = True
                    break
            if ok:
                break
        if not ok:
            print("FAILED  ", name, "- put it in cache/fonts manually")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
