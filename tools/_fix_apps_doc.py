import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "APPS.md")
s = open(p, encoding="utf-8").read()

repl = [
    ("`PATH` 含 `/usr/bin:/bin:/sbin:/system/bin`",
     "`PATH` 是 `/system/bin:/bin:/sbin`"),
    ("- 顶部显示「得分 / 最高分」；撞墙或撞自己显示「游戏结束 点击重新开始」。\n- 最高分保存在 `/data/snake.best`。",
     "- 顶部显示「得分 / 最高分」；撞墙或撞自己显示「游戏结束 点击重新开始」。\n- 最高分只在内存里，退出应用就清零。"),
    ("- 顶部「得分 x 最高 y」，最高分存 `/data/2048.best`；无路可走显示「游戏结束」，点「重来」重开。",
     "- 顶部「得分 x 最高 y」；最高分只在内存里，退出应用就清零。无路可走显示「游戏结束」，点「重来」重开。"),
    ("""  - `W A S D` / 方向键 —— 前后左右移动
  - `←` `→`（按住 Shift 时）或 `Q` `E` —— 转身
  - `PageUp` / `PageDown` —— 抬头/低头（鼠标上下拖动也行）
  - 鼠标左键 —— 挖掉准星下的方块
  - `空格` —— 放置当前手持方块
  - `E` 或右上「背包 (E)」—— 打开创造物品栏""",
     """  - `W` / `S` —— 前进、后退；`A` / `D` —— 左右平移
  - `↑` / `↓` —— 也是前后；`←` / `→` —— 转身
  - `PageUp` / `PageDown` —— 抬头 / 低头（鼠标上下拖动也行）
  - 鼠标左键 —— 挖掉准星下的方块
  - `空格` —— 放置当前手持方块
  - `1` ~ `5` —— 快捷栏选方块
  - `E` 或右上「背包 (E)」—— 打开创造物品栏；`Esc` 或再按 `E` 关闭
  - `Esc` —— 退出应用"""),
    ("- 10×10，10 颗雷；点格子挖开，右键/「切换标记」插旗。",
     "- 10×10，10 颗雷；点格子挖开，点底部「切换标记」进入插旗模式。"),
]

for a, b in repl:
    if a not in s:
        print("MISS:", a[:40])
    s = s.replace(a, b)

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("updated")
