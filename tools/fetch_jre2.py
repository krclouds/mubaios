import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
DST = os.path.join(CACHE, "jre17.tar.gz")
os.makedirs(CACHE, exist_ok=True)

LINK = ("https://github.com/adoptium/temurin17-binaries/releases/download/"
        "jdk-17.0.21%2B9/OpenJDK17U-jre_x64_linux_hotspot_17.0.21_9.tar.gz")
EXPECT = 44.6 * 1024 * 1024

ROUTES = [
    "https://ghfast.top/" + LINK,
    "https://ghproxy.net/" + LINK,
    LINK,
]


def fetch(url, dst, timeout=240):
    req = urllib.request.Request(url, headers={"User-Agent": "python"})
    got = 0
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dst, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if got % (10 << 20) < (1 << 20):
                print("  %.1f MB in %.0fs" % (got / 1048576, time.time() - t0), flush=True)
    return got


for url in ROUTES:
    host = url.split("/")[2]
    try:
        print("trying", host, flush=True)
        n = fetch(url, DST)
        if n < EXPECT * 0.9:
            print("short read", n)
            continue
        print("ok", host, round(n / 1048576, 1), "MB")
        break
    except Exception as e:
        print("fail", host, type(e).__name__, e, flush=True)
        if os.path.exists(DST):
            os.unlink(DST)
