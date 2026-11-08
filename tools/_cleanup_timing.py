import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# 1) drop the per-event debug print
s = re.sub(r"\n\t*fprintf\(stderr, \"EVDBG[^\n]*\n", "\n", s)

# 2) drop the section timers block inside draw_home
s = s.replace("""	struct timespec s0;
	double tw, tb, ts, ti;
#define SEC_NOW() clock_gettime(CLOCK_MONOTONIC, &s0)
#define SEC_MS() ((double)(s0.tv_sec * 1000.0 + s0.tv_nsec / 1e6))
	double p0, p1;

	SEC_NOW(); p0 = SEC_MS();
""", "")
s = s.replace("""	SEC_NOW(); p1 = SEC_MS(); tw = p1 - p0; p0 = p1;
""", "")
s = s.replace("""	SEC_NOW(); p1 = SEC_MS(); tb = p1 - p0; p0 = p1;
""", "")
s = s.replace("""	SEC_NOW(); p1 = SEC_MS(); ti = p1 - p0; p0 = p1;
""", "")
s = s.replace("""	SEC_NOW(); ts = SEC_MS() - p0;
	fprintf(stderr, "SEC_MS wall=%.1f bar=%.1f icons=%.1f dock=%.1f\\n", tw, tb, ti, ts);
""", "")

# 3) drop the manual flush timing wrapper, restore the plain flush+draw
s = s.replace("""	{
		struct timespec f0, f1;

		clock_gettime(CLOCK_MONOTONIC, &f0);
		nova_flush(fb);
		clock_gettime(CLOCK_MONOTONIC, &f1);
		fprintf(stderr, "FLUSH_MS %.1f\\n", (f1.tv_sec - f0.tv_sec) * 1000.0 +
			(f1.tv_nsec - f0.tv_nsec) / 1e6);
	}
""", "")

# 4) remove DRAW_MS / HOVER_MS / TICK_MS reporting
s = re.sub(r"\n\t*clock_gettime\(CLOCK_MONOTONIC, &t1\);\n\t*fprintf\(stderr, \"DRAW_MS[^\n]*\n\t*\(t1\.tv_nsec[^\n]*\n", "\n", s)
s = re.sub(r"\n\t*clock_gettime\(CLOCK_MONOTONIC, &h1\);\n\t*fprintf\(stderr, \"HOVER_MS[^\n]*\n\t*\(h1\.tv_nsec[^\n]*\n", "\n", s)
s = re.sub(r"\n\t*clock_gettime\(CLOCK_MONOTONIC, &t1\);\n\t*fprintf\(stderr, \"TICK_MS[^\n]*\n\t*\(t1\.tv_nsec[^\n]*\n", "\n", s)

# 5) remove the now-unused local timing variables
s = s.replace("\tstruct timespec t0, t1;\n\n\tclock_gettime(CLOCK_MONOTONIC, &t0);\n", "")
s = s.replace("\tstruct timespec h0, h1;\n\n\tclock_gettime(CLOCK_MONOTONIC, &h0);\n", "")
s = s.replace("\tstruct timespec t0, t1;\n\n", "")

open(SS, "w", encoding="utf-8", newline="\n").write(s)

left = [k for k in ("DRAW_MS", "HOVER_MS", "TICK_MS", "FLUSH_MS", "SEC_MS", "EVDBG", "PTRDBG") if k in s]
print("remaining debug markers:", left)
