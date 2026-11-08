"""Replace the v0.1 release asset with the freshly built ISO."""

import json
import os
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH = os.path.join(ROOT, "incoming", "gh", "bin", "gh.exe")
OWNER, REPO = "krclouds", "mubaios"
TOKEN = subprocess.check_output([GH, "auth", "token"], text=True).strip()
ISO = os.path.join(ROOT, "out", "mubaios-0.1-x86_64.iso")
NAME = "mubaiOS-0.1-x86_64.iso"


def req(method, url, payload=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    if data:
        r.add_header("Content-Type", ctype)
    with urllib.request.urlopen(r, timeout=300) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


rel = [r for r in req("GET", f"https://api.github.com/repos/{OWNER}/{REPO}/releases") if r["tag_name"] == "v0.1"][0]
for asset in rel["assets"]:
    req("DELETE", f"https://api.github.com/repos/{OWNER}/{REPO}/releases/assets/{asset['id']}")
    print("deleted old asset", asset["name"], asset["size"])

with open(ISO, "rb") as fh:
    data = fh.read()
up = req("POST",
         f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{rel['id']}/assets?name={NAME}",
         raw=data, ctype="application/octet-stream")
print("uploaded", up["name"], up["size"], up["browser_download_url"])
