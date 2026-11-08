import urllib.error
import urllib.request

NAME = "starcloud-launcher-linux_0.3.8-beta.8_amd64.deb"
IMG = "Starcloud%20Launcher-0.3.8-beta.8.AppImage"
CANDIDATES = [
    "https://starcloudfur.cn/downloads/" + NAME,
    "https://starcloudfur.cn/downloads/" + IMG,
    "https://starcloud.cn-nb1.rains3.com/downloads/" + NAME,
    "https://starcloud.cn-nb1.rains3.com/site/downloads/" + NAME,
    "https://starcloudfur.cn/v1/downloads/stats",
]

for url in CANDIDATES:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=40)
        print(r.status, r.headers.get("Content-Length"), r.geturl())
    except urllib.error.HTTPError as e:
        print(e.code, "HTTPError", url)
    except Exception as e:
        print("ERR", type(e).__name__, url, e)
