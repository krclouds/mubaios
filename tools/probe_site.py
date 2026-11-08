import re
import urllib.request

for url in ["https://starcloudfur.cn/", "http://starcloudfur.cn/", "https://starcloudfur.cn/download"]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=40)
        body = r.read().decode("utf-8", "ignore")
        print(url, r.status, len(body))
        links = re.findall(r"""href=["']([^"']+)["']""", body)
        for link in links[:60]:
            print("  ", link)
        print("  title:", re.findall(r"<title>(.*?)</title>", body)[:1])
    except Exception as e:
        print("ERR", url, type(e).__name__, e)
