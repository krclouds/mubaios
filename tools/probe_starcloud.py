import json
import socket
import urllib.request


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=40))


for repo in ["xingmiaobjm/Starcloud-Minecraft-Launcher-for-linux",
             "xingmiaobjm/Starcloud-Minecraft-Launcher"]:
    print("==", repo)
    try:
        rel = api("https://api.github.com/repos/%s/releases" % repo)
        print("  releases:", len(rel))
        for r in rel[:5]:
            print("   ", r["tag_name"], [(a["name"], a["size"]) for a in r.get("assets", [])][:6])
    except Exception as e:
        print("  releases ERR", e)
    try:
        tags = api("https://api.github.com/repos/%s/tags" % repo)
        print("  tags:", [t["name"] for t in tags][:8])
    except Exception as e:
        print("  tags ERR", e)

for host in ["starcloudfur.cn", "www.starcloudfur.cn"]:
    try:
        print(host, socket.gethostbyname(host))
    except Exception as e:
        print(host, "DNS ERR", e)
