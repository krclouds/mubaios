import urllib.error
import urllib.request

HOSTS = [
    "https://starcloud.cn-nb1.rains3.com/",
    "https://starcloud.cn-nb1.rains3.com/downloads/",
    "https://starcloud.cn-nb1.rains3.com/site/",
]
for url in HOSTS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=40)
        body = r.read(2000)
        print(r.status, url, len(body))
        print(body[:600])
    except urllib.error.HTTPError as e:
        print(e.code, url, e.read()[:200])
    except Exception as e:
        print("ERR", url, e)
