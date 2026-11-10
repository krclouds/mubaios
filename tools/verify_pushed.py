"""Cryptographic proof: local files vs the blobs GitHub stored.

Git blob ids are content-addressed, so if `git hash-object <file>` equals the
tree entry sha returned by the API, GitHub holds byte-identical content.
"""

import json
import os
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH = os.path.join(ROOT, "incoming", "gh", "bin", "gh.exe")
GIT = os.path.join(ROOT, "incoming", "PortableGit", "bin", "git.exe")
TOKEN = subprocess.check_output([GH, "auth", "token"], text=True).strip()

CHECK = ["LICENSE", "OPEN_SOURCE.md", "APPS.md", "README.md", "THIRD_PARTY.md", "build.py",
         "src/init.c", "src/system_server.c", "docs/screenshots/home.png"]


def api(path):
    r = urllib.request.Request("https://api.github.com" + path)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    return json.loads(urllib.request.urlopen(r, timeout=30).read())


tree = api("/repos/krclouds/mubaios/git/trees/main?recursive=1")
remote = {x["path"]: x["sha"] for x in tree["tree"] if x["type"] == "blob"}

rows = []
for path in CHECK:
    local = subprocess.check_output(
        [GIT, "-C", ROOT, "hash-object", path.replace("/", os.sep)], text=True).strip()
    got = remote.get(path)
    rows.append((path, local[:10], got[:10] if got else "MISSING", "MATCH" if local == got else "DIFF"))

width = max(len(r[0]) for r in rows)
print(f"{'file'.ljust(width)}  local blob  github blob  result")
for path, a, b, verdict in rows:
    print(f"{path.ljust(width)}  {a}    {b}     {verdict}")

line = "hash audit: " + ", ".join(f"{p}={v}" for p, _, _, v in rows)
with open(os.path.join(ROOT, "out", "proof", "evidence.txt"), "a", encoding="utf-8") as fh:
    fh.write("\n" + line + "\n")
print(line)
