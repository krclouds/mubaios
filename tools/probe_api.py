import json
import urllib.error
import urllib.request

BASE = "https://starcloudfur.cn"
NAME = "starcloud-launcher-linux_0.3.8-beta.8_amd64.deb"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=60)
    return r.status, r.read()


status, body = get(BASE + "/v1/downloads/stats")
print(status, body[:400])

for path in ["/v1/downloads/" + NAME, "/download/" + NAME, "/downloads/linux/" + NAME,
             "/v1/downloads/linux", "/v1/downloads"]:
    try:
        s, b = get(BASE + path)
        print(s, path, b[:200])
    except urllib.error.HTTPError as e:
        print(e.code, path)
    except Exception as e:
        print("ERR", path, e)
