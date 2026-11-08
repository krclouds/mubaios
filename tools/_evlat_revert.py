import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# remove the aborted latency probe wrapper
s = s.replace("""		{
			struct timespec e0, e1;
			static double acc;
			static int cnt;

			clock_gettime(CLOCK_MONOTONIC, &e0);
		if (nova_poll(&in, &ev, 250) == 0) {""",
              """		if (nova_poll(&in, &ev, 250) == 0) {""", 1)

s = s.replace("""		clock_gettime(CLOCK_MONOTONIC, &e1);
		acc += (e1.tv_sec - e0.tv_sec) * 1000.0 + (e1.tv_nsec - e0.tv_nsec) / 1e6;
		if (++cnt % 50 == 0)
			fprintf(stderr, "EVLAT n=%d avg=%.2fms\\n", cnt, acc / 50), acc = 0;
		}}
	}""",
              """		}
	}""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("reverted:", "e0" not in s and "EVLAT" not in s)
