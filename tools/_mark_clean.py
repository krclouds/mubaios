import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVA_C = os.path.join(ROOT, "src", "nova.c")
NOVA_H = os.path.join(ROOT, "src", "nova.h")
SS = os.path.join(ROOT, "src", "system_server.c")

s = open(NOVA_C, encoding="utf-8").read()
if "void nova_mark_clean" not in s:
    s = s.replace("void nova_flush(NovaFB *fb)\n{",
                  "void nova_mark_clean(void)\n{\n\tfb_dirty = 0;\n}\n\nvoid nova_flush(NovaFB *fb)\n{", 1)
    open(NOVA_C, "w", encoding="utf-8", newline="\n").write(s)

h = open(NOVA_H, encoding="utf-8").read()
if "nova_mark_clean" not in h:
    h = h.replace("void nova_flush(NovaFB *fb);",
                  "void nova_flush(NovaFB *fb);\nvoid nova_mark_clean(void);", 1)
    open(NOVA_H, "w", encoding="utf-8", newline="\n").write(h)

ss = open(SS, encoding="utf-8").read()
# after an explicit partial flush, the buffer is clean, so draw_cursor will not full-flush
ss = ss.replace("\tnova_flush_rect(fb, rx, ry, rw, rh);\n}",
                "\tnova_flush_rect(fb, rx, ry, rw, rh);\n\tnova_mark_clean();\n}", 1)
ss = ss.replace("\tnova_flush_rect(fb, 0, 0, fb->w, 56);",
                "\tnova_flush_rect(fb, 0, 0, fb->w, 56);\n\tnova_mark_clean();", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(ss)
print("mark_clean:", ss.count("nova_mark_clean"), "helper:", "void nova_mark_clean" in open(NOVA_C, encoding="utf-8").read())
