import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

if "EVLAT" not in s:
    # accumulate time spent handling each polled event
    s = s.replace("""		if (nova_poll(&in, &ev, 250) == 0) {""",
                  """		{
			struct timespec e0, e1;
			static double acc;
			static int cnt;

			clock_gettime(CLOCK_MONOTONIC, &e0);
		if (nova_poll(&in, &ev, 250) == 0) {""", 1)

    # close the measurement at the end of each loop iteration
    s = s.replace("""		switch (ev.type) {
		case NOVA_MOVE: {""",
                  """		switch (ev.type) {
		case NOVA_MOVE: {""", 1)

    # measure right before the loop restarts: find the end of the event switch
    s = s.replace("""			break;
		}
		default:
			break;
		}
	}""",
                  """			break;
		}
		default:
			break;
		}
		clock_gettime(CLOCK_MONOTONIC, &e1);
		acc += (e1.tv_sec - e0.tv_sec) * 1000.0 + (e1.tv_nsec - e0.tv_nsec) / 1e6;
		if (++cnt % 50 == 0)
			fprintf(stderr, "EVLAT n=%d avg=%.2fms\\n", cnt, acc / 50), acc = 0;
		}}
	}""", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("latency probe:", "EVLAT" in s)
