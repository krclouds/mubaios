import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVA_C = os.path.join(ROOT, "src", "nova.c")

DICT = r'''
struct tr_pair { const char *zh, *en; };

static const struct tr_pair tr_table[] = {
	{"设置", "Settings"}, {"文件", "Files"}, {"画板", "Paint"}, {"终端", "Terminal"},
	{"应用商店", "App Store"}, {"时钟", "Clock"}, {"计算器", "Calculator"},
	{"贪吃蛇", "Snake"}, {"迷你世界", "Mini World"}, {"日历", "Calendar"},
	{"天气", "Weather"}, {"相册", "Gallery"}, {"钢琴", "Piano"}, {"便签", "Notes"},
	{"扫雷", "Minesweeper"}, {"秒表", "Stopwatch"}, {"系统监视", "System Monitor"},
	{"指南针", "Compass"}, {"关于", "About"}, {"关于设备", "About device"},
	{"型号、内核与内存", "Model, kernel and memory"}, {"显示", "Display"},
	{"分辨率与像素格式", "Resolution and pixel format"}, {"已安装应用", "Installed apps"},
	{"/apps 中的应用", "Apps in /apps"}, {"关机", "Power off"},
	{"关闭计算机", "Shut the machine down"}, {"语言", "Language"},
	{"面板", "Panel"}, {"像素", "pixels"}, {"像素格式", "Pixel format"},
	{"驱动", "Driver"}, {"颜色测试", "Colour test"}, {"正在关机…", "Powering off..."},
	{"内核", "Kernel"}, {"架构", "Architecture"}, {"帧缓冲", "Framebuffer"},
	{"内存", "Memory"}, {"根文件系统", "Root filesystem"},
	{"initramfs（内存）", "initramfs (in memory)"},
	{"基于 Linux 内核的类 Android 系统", "An Android-shaped system on the Linux kernel"},
	{"自研用户态 + Linux 内核的类 Android 系统", "Custom user space on the Linux kernel"},
	{"基于 Linux 内核，用户态全部自研", "Linux kernel, user space written from scratch"},
	{"5 个预装 + 应用商店", "5 preinstalled + App Store"},
	{"欢迎回来", "Welcome back"}, {"没有最近的应用", "No recent apps"},
	{"查看器", "Viewer"}, {"空目录", "empty directory"},
	{"(二进制或空文件)", "(binary or empty file)"},
	{"输入命令，回车执行", "Type a command, Enter to run"},
	{"键盘", "Keyboard"}, {"空格", "Space"}, {"退格", "Backspace"},
	{"回车", "Enter"}, {"小写", "Shift"}, {"大写", "SHIFT"},
	{"NovaOS 0.1 终端", "NovaOS 0.1 terminal"},
	{"命令经由 /bin/sh (BusyBox) 执行", "Commands run through /bin/sh (BusyBox)"},
	{"试试：uname -a、ls /apps、free", "Try: uname -a, ls /apps, free"},
	{"没有实体键盘时，点右上角「键盘」用鼠标输入", "No hardware keyboard? Tap the keyboard button"},
	{"用手指或鼠标绘制 · 可撤销", "Draw with a finger or the mouse"},
	{"撤销", "Undo"}, {"清空", "Clear"}, {"输入算式", "Enter an expression"},
	{"游戏结束", "Game over"}, {"点击重新开始", "Tap to restart"},
	{"背包 (E)", "Inventory (E)"}, {"创造模式物品栏", "Creative inventory"},
	{"E 关闭", "E to close"}, {"该分类暂无物品", "No items in this category"},
	{"NovaOS 的方块世界还没有这一栏的内容", "This tab has no blocks yet"},
	{"全部", "All"}, {"刷怪蛋", "Spawn eggs"}, {"武器与战斗", "Weapons"},
	{"工具与采集", "Tools"}, {"护甲与装备", "Armour"}, {"食物与农业", "Food"},
	{"药水与炼药", "Potions"}, {"运输与容器", "Transport"}, {"书籍与导航", "Books"},
	{"装饰与纹样", "Decoration"}, {"音乐与收藏", "Music"}, {"材料与矿物", "Materials"},
	{"放置与实体", "Blocks"}, {"功能与特殊物品", "Special"},
	{"草方块", "Grass"}, {"泥土", "Dirt"}, {"石头", "Stone"}, {"圆石", "Cobblestone"},
	{"沙子", "Sand"}, {"沙砾", "Gravel"}, {"原木", "Log"}, {"木板", "Planks"},
	{"树叶", "Leaves"}, {"水", "Water"}, {"冰", "Ice"}, {"雪", "Snow"},
	{"玻璃", "Glass"}, {"砖块", "Bricks"}, {"煤炭矿石", "Coal ore"},
	{"铁矿石", "Iron ore"}, {"金矿石", "Gold ore"}, {"钻石矿石", "Diamond ore"},
	{"羊毛", "Wool"}, {"黑曜石", "Obsidian"}, {"熔岩", "Lava"},
	{"北京", "Beijing"}, {"演示数据 · 无网络", "Demo data · offline"},
	{"刷新", "Refresh"}, {"今天", "Today"}, {"明天", "Tomorrow"},
	{"第三天", "Day 3"}, {"第四天", "Day 4"}, {"第五天", "Day 5"},
	{"晴", "Sunny"}, {"多云", "Cloudy"}, {"小雨", "Light rain"}, {"阴", "Overcast"},
	{"日落", "Sunset"}, {"群山", "Mountains"}, {"海面", "Sea"}, {"城市", "City"},
	{"圆", "Circles"}, {"森林", "Forest"},
	{"点击琴键 · 本机暂无音频驱动，仅演示交互", "Tap the keys · no audio driver yet"},
	{"键盘输入 · Esc 保存并退出", "Type with the keyboard · Esc saves and exits"},
	{"点这里……其实请直接用键盘输入", "Empty note. Just start typing."},
	{"切换标记", "Toggle flag"}, {"重来", "Restart"},
	{"扫雷成功", "Cleared!"}, {"踩到地雷", "Boom!"},
	{"点「重来」再开一局", "Tap Restart to play again"}, {"旗", "F"},
	{"点「重来」继续", "Tap Restart to continue"}, {"方向键移动", "Arrow keys to move"},
	{"开始", "Start"}, {"暂停", "Pause"}, {"重置", "Reset"},
	{"负载 (1/5/15 分钟)", "Load (1/5/15 min)"}, {"CPU 核心", "CPU cores"},
	{"北", "N"}, {"东", "E"}, {"南", "S"}, {"西", "W"},
	{"左右拖动旋转表盘", "Drag left/right to rotate"},
	{"安装", "Install"}, {"打开", "Open"}, {"卸", "Del"},
	{"设", "S"}, {"文", "F"}, {"画", "P"}, {"终", "T"}, {"店", "M"},
	{"钟", "C"}, {"算", "="}, {"蛇", "S"}, {"界", "W"}, {"历", "D"},
	{"天", "W"}, {"相", "G"}, {"乐", "M"}, {"签", "N"}, {"雷", "X"},
	{"数", "2"}, {"秒", "T"}, {"监", "M"}, {"针", "C"}, {"关", "i"},
};

static int lang_cache = -1;

void nova_lang_reload(void)
{
	lang_cache = -1;
}

int nova_lang(void)
{
	if (lang_cache < 0) {
		FILE *f = fopen("/data/settings.conf", "r");
		char line[64];

		lang_cache = 0;
		while (f && fgets(line, sizeof(line), f))
			if (strncmp(line, "lang=en", 7) == 0)
				lang_cache = 1;
		if (f)
			fclose(f);
	}
	return lang_cache;
}

const char *nova_tr(const char *s)
{
	if (!nova_lang() || !s)
		return s;
	for (size_t i = 0; i < sizeof(tr_table) / sizeof(tr_table[0]); i++)
		if (strcmp(tr_table[i].zh, s) == 0)
			return tr_table[i].en;
	return s;
}
'''


def main():
    s = io.open(NOVA_C, encoding="utf-8").read()
    if "tr_table" not in s:
        s = s.replace('#include "font_cjk.h"', '#include "font_cjk.h"\n' + DICT, 1)
    s = s.replace(
        "int nova_text_width(const char *s, int scale)\n{\n\tconst unsigned char *p = (const unsigned char *)s;",
        "int nova_text_width(const char *s, int scale)\n{\n\tconst unsigned char *p;\n\n\ts = nova_tr(s);\n\tp = (const unsigned char *)s;")
    s = s.replace(
        "void nova_text(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale)\n{\n\tconst unsigned char *p = (const unsigned char *)s;",
        "void nova_text(NovaFB *fb, int x, int y, const char *s, uint32_t color, int scale)\n{\n\tconst unsigned char *p;\n\n\ts = nova_tr(s);\n\tp = (const unsigned char *)s;")
    io.open(NOVA_C, "w", encoding="utf-8").write(s)
    print("nova.c patched")


if __name__ == "__main__":
    main()
