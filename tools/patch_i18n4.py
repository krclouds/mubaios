import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

EXTRA = r'''	{"大字号时钟与日期", "Big clock and date"},
	{"加减乘除四则运算", "Basic arithmetic"},
	{"方向键控制的经典小游戏", "Classic snake game"},
	{"方块沙盒", "Block sandbox"},
	{"月历", "Month view"},
	{"五日预报", "5-day forecast"},
	{"程序化画作", "Procedural art"},
	{"八键琴演示", "Eight-key piano"},
	{"纯文本记事", "Plain text notes"},
	{"10×10 扫雷", "10x10 minesweeper"},
	{"合并数字", "Merge the numbers"},
	{"计时工具", "Stopwatch"},
	{"负载与内存", "Load and memory"},
	{"拖动旋转", "Drag to rotate"},
	{"系统信息", "System info"},
'''

p = os.path.join(SRC, "nova.c")
s = io.open(p, encoding="utf-8").read()
if "Big clock and date" not in s:
    s = s.replace("\t{\"设\", \"S\"},", EXTRA + "\t{\"设\", \"S\"},")
io.open(p, "w", encoding="utf-8").write(s)

p = os.path.join(SRC, "store.c")
s = io.open(p, encoding="utf-8").read()
s = s.replace('''		nova_text(fb, x + 92, y + 18, it->name, NOVA_WHITE, 2);''',
              '''		nova_text(fb, x + 92, y + 18, it->name, NOVA_WHITE,
			  nova_text_width(it->name, 2) > cw - 210 ? 1 : 2);''')
io.open(p, "w", encoding="utf-8").write(s)
print("store translations and adaptive name scale added")
