import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 面板底部留出 34px 条带给提示行
old = """        NeedH = y + 12;
        settings.Size = new Size(434, NeedH - 4);"""
new = """        y += 34;                    // 底部条带：让 shell 上的那行提示有地方待，不会压住内容
        NeedH = y + 12;
        settings.Size = new Size(434, NeedH - 4);"""
assert old in s, "FillSettings tail"
s = s.replace(old, new, 1)

# 面板高度扣掉条带；提示贴在条带里
old = """            shell.Size = new Size(438, need);
            settings.Size = new Size(434, need - 30);"""
new = """            shell.Size = new Size(438, need);
            settings.Size = new Size(434, need - 34);"""
assert old in s, "LayoutWindow else"
s = s.replace(old, new, 1)

s = s.replace("tipLabel.Location = new Point(16, Math.Max(0, shell.Height - 30));",
              "tipLabel.Location = new Point(16, Math.Max(0, shell.Height - 26));", 1)

p.write_text(s, encoding="utf-8")
print("tip strip reserved")
