import json
import urllib.parse
import urllib.request

QUERIES = [
    "minecraft launcher cli",
    "minecraft launcher terminal",
    "minecraft launcher headless",
    "minecraft launcher linux framebuffer",
    "minecraft launcher rust",
]


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=40))


for q in QUERIES:
    url = "https://api.github.com/search/repositories?q=%s&sort=stars&per_page=6" % urllib.parse.quote(q)
    try:
        d = api(url)
        print("==", q)
        for it in d.get("items", []):
            print("   %-45s %5d  %s  %s" % (it["full_name"], it["stargazers_count"],
                                            it.get("language"), (it.get("description") or "")[:60]))
    except Exception as e:
        print("ERR", q, e)
