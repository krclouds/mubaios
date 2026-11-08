import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs):
    p = os.path.join(SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s:
            print("MISS", name, a[:60])
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


patch("settings.c", [
    ('''				} else if (row == 2) {
					view = VIEW_APPS;
					REDRAW(draw_apps(&fb));
				} else {''',
     '''				} else if (row == 2) {
					view = VIEW_APPS;
					REDRAW(draw_apps(&fb));
				} else if (row == 3) {
					FILE *cfg = fopen("/data/settings.conf", "w");
					if (cfg) {
						fprintf(cfg, "lang=%s\\n", nova_lang() ? "zh" : "en");
						fclose(cfg);
					}
					nova_lang_reload();
					REDRAW(draw_list(&fb));
				} else {'''),
    ('static const char *titles[] = {"关于设备", "显示", "已安装应用", "关机"};',
     'static const char *titles[] = {"关于设备", "显示", "已安装应用", "语言", "关机"};'),
    ('static const char *subs[] = {\n\t\t"型号、内核与内存",\n\t\t"分辨率与像素格式",\n\t\t"/apps 中的应用",\n\t\t"关闭计算机",\n\t};',
     'static const char *subs[] = {\n\t\t"型号、内核与内存",\n\t\t"分辨率与像素格式",\n\t\t"/apps 中的应用",\n\t\t"中文 / English",\n\t\t"关闭计算机",\n\t};'),
    ('for (int i = 0; i < 4; i++) {\n\t\tuint32_t bg = (i == 3) ? 0x3a1620 : 0x1b2030;',
     'for (int i = 0; i < 5; i++) {\n\t\tuint32_t bg = (i == 4) ? 0x3a1620 : 0x1b2030;'),
    ('nova_text(fb, 92, y + 20, titles[i], i == 3 ? 0xff8a8a : NOVA_WHITE, 2);',
     'nova_text(fb, 92, y + 20, titles[i], i == 4 ? 0xff8a8a : NOVA_WHITE, 2);'),
    ('if (ev.x < 60 || ev.x > fb.w - 60 || ev.y < 170 || row > 3)',
     'if (ev.x < 60 || ev.x > fb.w - 60 || ev.y < 170 || row > 4)'),
])

patch("system_server.c", [
    ('''	{ static const char *wd[] = {"日","一","二","三","四","五","六"};
	  snprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday, wd[tm.tm_wday]); }''',
     '''	if (nova_lang()) {
		strftime(date, sizeof(date), "%a, %d %b", &tm);
	} else {
		static const char *wd[] = {"日", "一", "二", "三", "四", "五", "六"};
		snprintf(date, sizeof(date), "%d月%d日 星期%s", tm.tm_mon + 1, tm.tm_mday, wd[tm.tm_wday]);
	}'''),
    ('''	waitpid(pid, NULL, 0);
	/* the store may have installed or removed apps while it ran */
	scan_apps();''',
     '''	waitpid(pid, NULL, 0);
	/* the store may have installed apps and Settings may have changed the
	 * language while it ran */
	nova_lang_reload();
	scan_apps();'''),
])

print("patched settings + system_server")
