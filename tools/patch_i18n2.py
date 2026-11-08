import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")


def patch(name, pairs, must=True):
    p = os.path.join(SRC, name)
    s = io.open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s and must:
            print("MISS", name, a[:50])
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8").write(s)


# --- settings: language row -------------------------------------------
patch("settings.c", [
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
    ('''				} else if (row == 2) {
					view = VIEW_APPS;
					draw_apps(&fb);
				} else {''',
     '''				} else if (row == 2) {
					view = VIEW_APPS;
					draw_apps(&fb);
				} else if (row == 3) {
					FILE *cfg = fopen("/data/settings.conf", "w");
					if (cfg) {
						fprintf(cfg, "lang=%s\\n", nova_lang() ? "zh" : "en");
						fclose(cfg);
					}
					nova_lang_reload();
					draw_list(&fb);
				} else {'''),
])

# --- system_server: reload language, localized date --------------------
patch("system_server.c", [
    ('strftime(date, sizeof(date), "%A, %d %B", &tm);',
     'strftime(date, sizeof(date), nova_lang() ? "%a, %d %b" : "%A, %d %B", &tm);'),
    ('''	waitpid(pid, NULL, 0);
	/* the store may have installed or removed apps while it ran */
	scan_apps();''',
     '''	waitpid(pid, NULL, 0);
	/* the store may have installed or removed apps, and Settings may have
	 * changed the language while it ran */
	nova_lang_reload();
	scan_apps();'''),
])

# --- formatted strings that the dictionary cannot match -----------------
patch("store.c", [
    ('snprintf(line, sizeof(line), "共 %d 个应用，已安装 %d 个", ITEM_N, count_installed());',
     'snprintf(line, sizeof(line), L("共 %d 个应用，已安装 %d 个", "%d apps, %d installed"), ITEM_N, count_installed());'),
])

patch("snake.c", [
    ('snprintf(buf, sizeof(buf), "得分 %d   最高 %d", score, best);',
     'snprintf(buf, sizeof(buf), L("得分 %d   最高 %d", "Score %d  Best %d"), score, best);'),
])

patch("game2048.c", [
    ('snprintf(buf, sizeof(buf), "得分 %d   最高 %d", score, best);',
     'snprintf(buf, sizeof(buf), L("得分 %d   最高 %d", "Score %d  Best %d"), score, best);'),
])

patch("minesweeper.c", [
    ('snprintf(buf, sizeof(buf), "已开 %d/%d   %s", opened, N * N - MINES,\n\t\t flag_mode ? "标记模式" : "挖掘模式");',
     'snprintf(buf, sizeof(buf), L("已开 %d/%d   %s", "Opened %d/%d   %s"), opened, N * N - MINES,\n\t\t flag_mode ? L("标记模式", "Flag mode") : L("挖掘模式", "Dig mode"));'),
    ('nova_text_center(fb, 170, 752, "切换标记", NOVA_WHITE, 2);',
     'nova_text_center(fb, 170, 752, L("切换标记", "Flag mode"), NOVA_WHITE, 2);'),
])

patch("sysmon.c", [
    ('snprintf(line, sizeof(line), "运行时间 %.0f 分 %.0f 秒", up / 60, (double)((long)up % 60));',
     'snprintf(line, sizeof(line), L("运行时间 %.0f 分 %.0f 秒", "Uptime %.0f min %.0f s"), up / 60, (double)((long)up % 60));'),
    ('nova_text(fb, 80, 260, "负载 (1/5/15 分钟)", NOVA_DIM, 2);',
     'nova_text(fb, 80, 260, L("负载 (1/5/15 分钟)", "Load (1/5/15 min)"), NOVA_DIM, 2);'),
    ('nova_text(fb, 80, 550, "CPU 核心", NOVA_DIM, 2);',
     'nova_text(fb, 80, 550, L("CPU 核心", "CPU cores"), NOVA_DIM, 2);'),
])

patch("calendar.c", [
    ('snprintf(buf, sizeof(buf), "%d年%d月", year, month);',
     'snprintf(buf, sizeof(buf), L("%d年%d月", "%d/%d"), year, month);'),
])

patch("world.c", [
    ('snprintf(line, sizeof(line), "FPS %.0f  坐标 %.0f,%.0f  高度 %d  手持 %s",\n\t\t fps, cam_x, cam_y, (int)cam_z, block_name[selected]);',
     'snprintf(line, sizeof(line), L("FPS %.0f  坐标 %.0f,%.0f  高度 %d  手持 %s",\n\t\t\t\t\t       "FPS %.0f  x %.0f y %.0f  h %d  hand %s"),\n\t\t fps, cam_x, cam_y, (int)cam_z, block_name[selected]);'),
    ('nova_text_center(fb, fb->w - 155, 98, "背包 (E)", NOVA_WHITE, 1);',
     'nova_text_center(fb, fb->w - 155, 98, L("背包 (E)", "Inventory (E)"), NOVA_WHITE, 1);'),
])

print("i18n call sites patched")
