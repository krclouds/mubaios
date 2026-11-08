import json
import urllib.request

REPOS = ["PrismLauncher/PrismLauncher", "HMCL-dev/HMCL", "Hex-Dragon/PCL2"]


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=40))


for repo in REPOS:
    print("==", repo)
    try:
        rel = api("https://api.github.com/repos/%s/releases/latest" % repo)
        print("  tag:", rel["tag_name"], rel["published_at"])
        for a in rel.get("assets", []):
            print("   %-70s %8.1f MB" % (a["name"], a["size"] / 1048576))
    except Exception as e:
        print("  ERR", e)
