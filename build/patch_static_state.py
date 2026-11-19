import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 字段
old = "    bool handedOff;"
new = "    bool handedOff;\n    bool staticOn;      // 静态模式：真系统光标已经换上去了（没有覆盖层）"
assert old in s
s = s.replace(old, new, 1)

# 2) 状态
old = "        bool on = overlay != null;\n        status.Text = on ? \"已变身\" : \"未变身\";"
new = "        bool on = overlay != null || staticOn;\n        status.Text = on ? \"已变身\" : \"未变身\";"
assert old in s
s = s.replace(old, new, 1)

# 3) Apply 静态分支
old = """            if (C.Mode == "static")
            {
                CursorSwitch.ApplyStatic();
                RefreshStatus();
                return;
            }"""
new = """            if (C.Mode == "static")
            {
                CursorSwitch.ApplyStatic();
                staticOn = true;
                RefreshStatus();
                return;
            }"""
assert old in s
s = s.replace(old, new, 1)

# 4) Restore
old = """            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }
            CursorSwitch.Restore();
            RefreshStatus();"""
new = """            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }
            CursorSwitch.Restore();
            staticOn = false;
            RefreshStatus();"""
assert old in s
s = s.replace(old, new, 1)

# 5) 关窗时也要把静态模式的真光标还回去
old = """        try { if (overlay != null) { overlay.Stop(); Thread.Sleep(220); CursorSwitch.Restore(); } } catch { }"""
new = """        try
        {
            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }
            if (CursorSwitch.Applied || staticOn) CursorSwitch.Restore();
            staticOn = false;
        }
        catch { }"""
assert old in s
s = s.replace(old, new, 1)

# 6) 关窗时若静态模式开着，Restore 之后界面状态也跟着复位（无窗可刷，忽略）

# 7) 文案：静态模式现在是真指针
s = s.replace('modeStatic.Sub = "打游戏用";', 'modeStatic.Sub = "真指针，打游戏用";')
s = s.replace('sub: "静态模式就用这一张，金币已经画在图里"', 'sub: "这张图会做成 32×32 的系统光标，金币已经画在图里"')

p.write_text(s, encoding="utf-8")
print("static mode wired to status/restore")
