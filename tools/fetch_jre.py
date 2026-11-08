import hashlib
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "python"})
    return urllib.request.urlopen(req, timeout=timeout).read()


api = ("https://api.adoptium.net/v3/assets/latest/17/hotspot"
       "?architecture=x64&image_type=jre&os=linux&vendor=eclipse")
data = json.loads(get(api).decode())
asset = data[0]["binary"]["package"]
link = asset["link"]
print("link:", link)
print("size:", round(asset["size"] / 1048576, 1), "MB")
print("checksum:", asset["checksum"])

blob = None
for url in [link, "https://ghfast.top/" + link, "https://ghproxy.net/" + link]:
    try:
        blob = get(url, timeout=600)
        print("ok from", url.split("/")[2], len(blob))
        break
    except Exception as e:
        print("fail", url.split("/")[2], type(e).__name__, e)

if blob is None:
    raise SystemExit("download failed")
if len(blob) != asset["size"]:
    print("WARN size mismatch", len(blob), asset["size"])
dst = os.path.join(CACHE, "jre17.tar.gz")
open(dst, "wb").write(blob)
print("sha256", hashlib.sha256(blob).hexdigest())
