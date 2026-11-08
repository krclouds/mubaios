import io
import re
import urllib.request

BASE = "https://starcloudfur.cn"
OUT = "starcloud_js_scan.txt"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")


html = get(BASE + "/")
scripts = re.findall(r"""src=["']([^"']+\.js)["']""", html)
lines = ["scripts: %r" % scripts]
for s in scripts:
    js = get(BASE + s if s.startswith("/") else s)
    lines.append("== %s %d" % (s, len(js)))
    for pat in [r"https?://[^\"'\s)<>]+",
                r"/api/[^\"'\s)<>]+",
                r"[\"'][^\"']{0,60}(?:download|Download|release|Release)[^\"']{0,60}[\"']"]:
        found = sorted(set(re.findall(pat, js)))
        lines.append("  pattern %s -> %d hits" % (pat, len(found)))
        for f in found[:40]:
            lines.append("    " + f)
io.open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("written", OUT)
