import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVA = os.path.join(ROOT, "src", "nova.c")
s = open(NOVA, encoding="utf-8").read()

old = """			d = isqrt_i(d2);
			a = alpha * (r - d) / r;
			a = a * a / 255;"""
new = """			a = alpha * (r2 - d2) / r2;
			a = a * a / 255;"""
if old in s:
    s = s.replace(old, new, 1)
    s = s.replace("\t\t\tint dx, dy, d, a, d2;", "\t\t\tint dx, dy, a, d2;", 1)
    s = s.replace("\t\t\tif (d2 > r2)\n\t\t\t\tcontinue;\n", "\t\t\tif (d2 > r2)\n\t\t\t\tcontinue;\n", 1)

open(NOVA, "w", encoding="utf-8", newline="\n").write(s)
print("glow uses squared falloff:", "alpha * (r2 - d2) / r2" in s, "| isqrt gone from glow:", "isqrt_i(d2)" not in s)
