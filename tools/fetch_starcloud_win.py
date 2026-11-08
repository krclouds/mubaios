import hashlib
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING = os.path.join(ROOT, "incoming")
os.makedirs(INCOMING, exist_ok=True)

URL = ("https://starcloudfur.cn/downloads/"
       "Starcloud%20Minecraft%20Launcher_0.3.9_x64-setup-20261022-201150.exe")
DST = os.path.join(INCOMING, "Starcloud-Minecraft-Launcher_0.3.9_x64-setup.exe")

if not os.path.exists(DST):
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=600).read()
    open(DST, "wb").write(data)
    print("downloaded", len(data), "bytes")

blob = open(DST, "rb").read()
print("size MB:", round(len(blob) / 1048576, 1))
print("sha256:", hashlib.sha256(blob).hexdigest())
print("pe:", blob[:2] == b"MZ")
print("nsis:", b"Nullsoft" in blob[:200000] or b"NSIS" in blob[:400000])
print("signed:", b"Winaero" in blob or b"signature" in blob[:200000])
