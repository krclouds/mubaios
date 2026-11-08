import hashlib
import io
import os
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)

URL = ("https://github.com/theorzr/portablemc/releases/download/v5.0.6/"
       "portablemc-5.0.6-linux-x86_64-gnu.tar.gz")
DST = os.path.join(CACHE, "portablemc.tar.gz")


def fetch(url, dst):
    routes = [
        url,
        "https://ghfast.top/" + url,
        "https://ghproxy.net/" + url,
    ]
    for r in routes:
        try:
            req = urllib.request.Request(r, headers={"User-Agent": "python"})
            data = urllib.request.urlopen(req, timeout=180).read()
            open(dst, "wb").write(data)
            print("ok", r.split("/")[2], len(data))
            return data
        except Exception as e:
            print("fail", r.split("/")[2], type(e).__name__)
    raise SystemExit("download failed")


blob = fetch(URL, DST)
print("sha256", hashlib.sha256(blob).hexdigest())

tar = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
names = tar.getnames()
print("members:", names[:10])
for m in tar.getmembers():
    if m.isfile() and (m.name.endswith("portablemc") or m.name.endswith("portablemc.exe")):
        data = tar.extractfile(m).read()
        print("binary:", m.name, len(data))
        libs = sorted(set(x.decode() for x in __import__("re").findall(rb"lib[a-zA-Z0-9_+.-]+\.so(?:\.\d+)*", data)))
        print("libs:", libs)
        out = os.path.join(CACHE, "portablemc")
        open(out, "wb").write(data)
        print("saved", out)
