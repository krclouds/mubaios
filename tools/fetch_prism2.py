import hashlib
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING = os.path.join(ROOT, "incoming")
os.makedirs(INCOMING, exist_ok=True)


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def try_get(url, headers=None, timeout=120):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "python"})
    return urllib.request.urlopen(req, timeout=timeout).read()


rel = api("https://api.github.com/repos/PrismLauncher/PrismLauncher/releases/latest")
tag = rel["tag_name"]
wanted = "PrismLauncher-Windows-MSVC-Portable-11.1.1.zip"
asset = next(a for a in rel["assets"] if a["name"] == wanted)
print("target", wanted, round(asset["size"] / 1048576, 1), "MB")

routes = [
    ("ghproxy", "https://ghproxy.net/https://github.com/PrismLauncher/PrismLauncher/releases/download/%s/%s" % (tag, wanted)),
    ("ghfast", "https://ghfast.top/https://github.com/PrismLauncher/PrismLauncher/releases/download/%s/%s" % (tag, wanted)),
    ("api", "https://api.github.com/repos/PrismLauncher/PrismLauncher/releases/assets/%s" % asset["id"]),
]

for name, url in routes:
    t0 = time.time()
    try:
        headers = {"User-Agent": "python"}
        if name == "api":
            headers["Accept"] = "application/octet-stream"
        blob = try_get(url, headers, timeout=180)
        print(name, "ok", len(blob), "in", round(time.time() - t0, 1), "s")
        dst = os.path.join(INCOMING, wanted)
        open(dst, "wb").write(blob)
        print("saved", dst)
        print("sha256", hashlib.sha256(blob).hexdigest())
        break
    except Exception as e:
        print(name, "fail", type(e).__name__, e, "after", round(time.time() - t0, 1), "s")
