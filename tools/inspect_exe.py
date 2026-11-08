import os
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "incoming", "Starcloud-Minecraft-Launcher_0.3.9_x64-setup.exe")

blob = open(PATH, "rb").read()
print("size", len(blob))

pe_off = struct.unpack_from("<I", blob, 0x3C)[0]
print("PE sig", blob[pe_off:pe_off + 4])
coff = pe_off + 4
num_sections = struct.unpack_from("<H", blob, coff + 2)[0]
opt_size = struct.unpack_from("<H", blob, coff + 16)[0]
opt = coff + 20
magic = struct.unpack_from("<H", blob, opt)[0]
print("optional magic", hex(magic), "sections", num_sections, "opt size", opt_size)
# data directories start at opt + 112 for PE32+, +96 for PE32
dd = opt + (112 if magic == 0x20B else 96)
sec_rva, sec_size = struct.unpack_from("<II", blob, dd + 4 * 8)
print("security dir (signature) rva/size:", sec_rva, sec_size)

for needle in [b"Nullsoft", b"NSIS", b"Tauri", b"WiX", b"Inno Setup", b"Starcloud", b"starcloud"]:
    print(needle, blob.find(needle))

for enc in ("utf-8", "utf-16le"):
    try:
        txt = blob.decode(enc, "ignore")
    except Exception:
        continue
    for probe in ["Starcloud", "starcloudfur", "Minecraft"]:
        i = txt.find(probe)
        if i >= 0:
            print(enc, probe, "->", txt[i:i + 80].replace("\x00", ""))
