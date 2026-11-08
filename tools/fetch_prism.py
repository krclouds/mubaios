import hashlib
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING = os.path.join(ROOT, "incoming")
os.makedirs(INCOMING, exist_ok=True)
NAME = "PrismLauncher-Windows-MinGW-w64-Setup-11.1.1.exe"
DST = os.path.join(INCOMING, NAME)


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


rel = api("https://api.github.com/repos/PrismLauncher/PrismLauncher/releases/latest")
asset = next(a for a in rel["assets"] if a["name"] == NAME)
print("asset id", asset["id"], round(asset["size"] / 1048576, 1), "MB")

candidates = [
    "https://api.github.com/repos/PrismLauncher/PrismLauncher/releases/assets/%s" % asset["id"],
    "https://ghproxy.net/https://github.com/PrismLauncher/PrismLauncher/releases/download/%s/%s" % (rel["tag_name"], NAME),
    "https://ghfast.top/https://github.com/PrismLauncher/PrismLauncher/releases/download/%s/%s" % (rel["tag_name"], NAME),
    "https://mirror.ghproxy.com/https://github.com/PrismLauncher/PrismLauncher/releases/download/%s/%s" % (rel["tag_name"], NAME),
]

blob = None
for url in candidates:
    try:
        headers = {"User-Agent": "python"}
        if "api.github.com" in url:
            headers["Accept"] = "application/octet-stream"
        req = urllib.request.Request(url, headers=headers)
        blob = urllib.request.urlopen(req, timeout=600).read()
        print("ok from", url.split("/")[2], len(blob))
        break
    except Exception as e:
        print("fail", url.split("/")[2], type(e).__name__, e)

if blob is None:
    raise SystemExit("all download routes failed")

open(DST, "wb").write(blob)
print("size MB:", round(len(blob) / 1048576, 1))
print("sha256:", hashlib.sha256(blob).hexdigest())
print("pe:", blob[:2] == b"MZ")
