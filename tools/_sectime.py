import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

if "SEC_MS" not in s:
    s = s.replace("""	if (!wall_buf)
		build_wallpaper(fb);
	else
		memcpy(fb->buf, wall_buf, wall_len * 4);

	android_status_bar(fb, clock, date);
	nova_text(fb, 56, 78, "欢迎回来", NOVA_WHITE, 3);
	draw_search(fb, 140);
""",
                  """	struct timespec s0;
	double tw, tb, ts, ti;
#define SEC_NOW() clock_gettime(CLOCK_MONOTONIC, &s0)
#define SEC_MS() ((double)(s0.tv_sec * 1000.0 + s0.tv_nsec / 1e6))
	double p0, p1;

	SEC_NOW(); p0 = SEC_MS();
	if (!wall_buf)
		build_wallpaper(fb);
	else
		memcpy(fb->buf, wall_buf, wall_len * 4);
	SEC_NOW(); p1 = SEC_MS(); tw = p1 - p0; p0 = p1;

	android_status_bar(fb, clock, date);
	nova_text(fb, 56, 78, "欢迎回来", NOVA_WHITE, 3);
	draw_search(fb, 140);
	SEC_NOW(); p1 = SEC_MS(); tb = p1 - p0; p0 = p1;
""", 1)

    s = s.replace("""	{
		int ms = max_scroll(fb);
""", """	SEC_NOW(); p1 = SEC_MS(); ti = p1 - p0; p0 = p1;
	{
		int ms = max_scroll(fb);
""", 1)

    s = s.replace("""	draw_dock(fb);
	if (shade)
		draw_shade(fb);""",
                  """	draw_dock(fb);
	if (shade)
		draw_shade(fb);
	SEC_NOW(); ts = SEC_MS() - p0;
	fprintf(stderr, "SEC_MS wall=%.1f bar=%.1f icons=%.1f dock=%.1f\\n", tw, tb, ti, ts);""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("sections:", "SEC_MS wall" in s)
