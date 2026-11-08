import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "src", "system_server.c")
s = open(SS, encoding="utf-8").read()

# the tick currently passes an undefined `date`; build one locally instead
if "draw_status_only(&fb, clock, date);" in s:
    s = s.replace("draw_status_only(&fb, clock, date);",
                  "draw_status_only(&fb, clock);", 1)

old_sig = "static void draw_status_only(NovaFB *fb, const char *clk, const char *dt)\n{"
new_sig = (
    "static void draw_status_only(NovaFB *fb, const char *clk)\n"
    "{\n"
    "\tchar date[64];\n"
    "\ttime_t now = time(NULL);\n"
    "\tstruct tm tm;\n\n"
    "\tlocaltime_r(&now, &tm);\n"
    "\tif (nova_lang()) {\n"
    '\t\tstrftime(date, sizeof(date), "%a, %d %b", &tm);\n'
    "\t} else {\n"
    '\t\tstatic const char *wd[] = {"日", "一", "二", "三", "四", "五", "六"};\n'
    '\t\tsnprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday, wd[tm.tm_wday]);\n'
    "\t}\n"
)
if old_sig in s:
    s = s.replace(old_sig, new_sig, 1)

s = s.replace("\tandroid_status_bar(fb, clk, dt);", "\tandroid_status_bar(fb, clk, date);", 1)

open(SS, "w", encoding="utf-8", newline="\n").write(s)
print("sig:", "draw_status_only(NovaFB *fb, const char *clk)\n{" in s,
      "call:", "draw_status_only(&fb, clock);" in s)
