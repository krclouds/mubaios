import re
import urllib.request

BASE = "https://starcloudfur.cn"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")


html = get(BASE + "/")
scripts = re.findall(r"""src=["']([^"']+\.js)["']""", html)
print("scripts:", scripts)
for s in scripts:
    js = get(BASE + s if s.startswith("/") else s)
    print("==", s, len(js))
    for pat in [r"https?://[^\"'\s]+\.(?:exe|deb|AppImage|zip|dmg)",
                r"[\"'][^\"']*?(?:download|release)[^\"']*?[\"']",
                r"/api/[^\"'\s]+"]:
        found = sorted(set(re.findall(pat, js)))[:25]
        if found:
            print("  ", pat, found)
