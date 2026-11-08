import urllib.error
import urllib.request

BASE = "https://starcloudfur.cn/downloads/"
NAMES = [
    "Starcloud Minecraft Launcher_0.3.9_x64-setup-20261022-201150.exe",
    "Starcloud Minecraft Launcher_0.3.9_x64-portable-20261022-201150.zip",
    "Starcloud Launcher-0.3.8-beta.8.AppImage",
    "starcloud-launcher-linux_0.3.8-beta.8_amd64.deb",
]
for n in NAMES:
    for enc in (n, urllib.parse.quote(n)):
        url = BASE + enc
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            r = urllib.request.urlopen(req, timeout=40)
            print(r.status, r.headers.get("Content-Length"), url)
        except urllib.error.HTTPError as e:
            print(e.code, url)
        except Exception as e:
            print("ERR", url, e)
