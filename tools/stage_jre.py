import io
import os
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "cache", "jre17.tar.gz")
DST = os.path.join(ROOT, "rootfs", "opt", "jdk")


def main():
    if not os.path.exists(SRC):
        raise SystemExit("missing " + SRC)
    if os.path.isdir(DST):
        import shutil
        shutil.rmtree(DST)
    os.makedirs(DST, exist_ok=True)

    tar = tarfile.open(SRC, "r:gz")
    members = tar.getmembers()
    top = members[0].name.split("/")[0]
    count = 0
    for m in members:
        rel = m.name
        if not rel.startswith(top):
            continue
        rel = rel[len(top):].lstrip("/")
        if not rel:
            continue
        target = os.path.join(DST, rel)
        if m.isdir():
            os.makedirs(target, exist_ok=True)
            continue
        if not m.isfile():
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = tar.extractfile(m).read()
        with open(target, "wb") as f:
            f.write(data)
        mode = 0o755 if (m.mode & 0o111) else 0o644
        try:
            os.chmod(target, mode)
        except OSError:
            pass
        count += 1
    print("extracted", count, "files to", DST)
    print("java binary:", os.path.exists(os.path.join(DST, "bin", "java")))


if __name__ == "__main__":
    main()
