import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs):
    p = os.path.join(SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s:
            print("MISS", name, a[:60].replace("\n", "\\n"))
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


# --- header: back buffer + flush ------------------------------------------
patch("nova.h", [
    ("	uint8_t *mem;", "	uint8_t *mem;\n	uint32_t *buf;"),
    ("void nova_fb_close(NovaFB *fb);", "void nova_fb_close(NovaFB *fb);\nvoid nova_flush(NovaFB *fb);"),
])

# --- implementation -------------------------------------------------------
patch("nova.c", [
    # allocate the RAM back buffer
    ("	fb->mem = mmap(NULL, fb->len, PROT_READ | PROT_WRITE, MAP_SHARED, fb->fd, 0);",
     "	fb->buf = calloc((size_t)fb->w * (size_t)fb->h, sizeof(uint32_t));\n"
     "	if (!fb->buf) {\n\t\tclose(fb->fd);\n\t\treturn -1;\n\t}\n"
     "	fb->mem = mmap(NULL, fb->len, PROT_READ | PROT_WRITE, MAP_SHARED, fb->fd, 0);"),
    # put_px -> back buffer
    ("""	if (fb->bpp == 32) {
		*(uint32_t *)(fb->mem + (size_t)y * fb->stride + (size_t)x * 4) = c;
	} else if (fb->bpp == 16) {""",
     """	if (fb->bpp == 32) {
		fb->buf[(size_t)y * fb->w + x] = c;
	} else if (fb->bpp == 16) {"""),
    # nova_get reads the back buffer
    ("""	if (fb->bpp == 32)
		return *(uint32_t *)(fb->mem + (size_t)y * fb->stride + (size_t)x * 4);""",
     """	if (fb->bpp == 32)
		return fb->buf[(size_t)y * fb->w + x];"""),
    # fill writes rows of the back buffer
    ("""		for (int yy = y0; yy < y1; yy++) {
			uint32_t *row = (uint32_t *)(fb->mem + (size_t)yy * fb->stride);
			for (int xx = x0; xx < x1; xx++)
				row[xx] = color;
		}""",
     """		for (int yy = y0; yy < y1; yy++) {
			uint32_t *row = fb->buf + (size_t)yy * fb->w;
			for (int xx = x0; xx < x1; xx++)
				row[xx] = color;
		}"""),
])

# add nova_flush right after nova_fill
p = os.path.join(SRC, "nova.c")
s = io.open(p, encoding="utf-8").read()
if "void nova_flush(NovaFB *fb)" not in s:
    flush = '''
void nova_flush(NovaFB *fb)
{
	if (!fb->buf || fb->bpp != 32)
		return;
	for (int y = 0; y < fb->h; y++)
		memcpy(fb->mem + (size_t)y * fb->stride,
		       fb->buf + (size_t)y * fb->w, (size_t)fb->w * 4);
}
'''
    s = s.replace("static int isqrt_i(int v)", flush + "\nstatic int isqrt_i(int v)", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("sdk back buffer done")
