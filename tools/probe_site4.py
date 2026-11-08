import io
import re
import urllib.request

BASE = "https://starcloudfur.cn"
JS = "/assets/index-CFKPcDF3.js"


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


js = get(BASE + JS)
io.open("starcloud_bundle.js", "w", encoding="utf-8").write(js)

lines = ["bundle %d bytes" % len(js)]
for needle in ["rains3", "cn-nb1", "site", "download", "version", ".exe", ".deb", "AppImage", "api"]:
    idx = [m.start() for m in re.finditer(re.escape(needle), js)][:6]
    lines.append("== %s (%d)" % (needle, len(idx)))
    for i in idx:
        lines.append("   ..." + js[max(0, i - 120):i + 160].replace("\n", " ") + "...")
io.open("starcloud_scan2.txt", "w", encoding="utf-8").write("\n".join(lines))
print("saved")
