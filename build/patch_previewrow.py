import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 新建两个“预览”小按钮（只换预览，不换光标）
old = """        applyBtn = new Btn { Text = "变身为动态挂件", Sub = "会晃，桌面用", Location = new Point(28, 596), Size = new Size(228, 66) };"""
new = """        previewDyn = new Btn { Text = "预览动态", Sub = "", Location = new Point(28, 550), Size = new Size(228, 34) };
        previewStatic = new Btn { Text = "预览静态", Sub = "", Location = new Point(270, 550), Size = new Size(228, 34) };
        applyBtn = new Btn { Text = "变身为动态挂件", Sub = "会晃，桌面用", Location = new Point(28, 596), Size = new Size(228, 66) };"""
assert old in s
s = s.replace(old, new, 1)

old = """        Controls.Add(applyBtn);
        Controls.Add(applyStaticBtn);"""
new = """        Controls.Add(previewDyn); Controls.Add(previewStatic);
        Controls.Add(applyBtn);
        Controls.Add(applyStaticBtn);"""
assert old in s
s = s.replace(old, new, 1)

old = """        applyBtn.Click += (a, b) => { if (C.Mode != "pendant") SetMode("pendant"); Apply(); };"""
new = """        previewDyn.Click += (a, b) => { if (C.Mode != "pendant") SetMode("pendant"); };
        previewStatic.Click += (a, b) => { if (C.Mode != "static") SetMode("static"); };
        applyBtn.Click += (a, b) => { if (C.Mode != "pendant") SetMode("pendant"); Apply(); };"""
assert old in s
s = s.replace(old, new, 1)

old = "    Btn applyBtn, applyStaticBtn, restoreBtn;"
new = "    Btn applyBtn, applyStaticBtn, restoreBtn, previewDyn, previewStatic;"
assert old in s
s = s.replace(old, new, 1)

# 2) 左列排版：预览行 -> 变身行 -> 恢复行
old = """        int btnTop = ClientSize.Height - 28 - 124;"""
new = """        int btnTop = ClientSize.Height - 28 - 170;"""
assert old in s
s = s.replace(old, new, 1)

old = """        applyBtn.Location = new Point(28, btnTop);
        applyStaticBtn.Location = new Point(270, btnTop);
        restoreBtn.Location = new Point(28, btnTop + 74);"""
new = """        previewDyn.Location = new Point(28, btnTop - 44);
        previewStatic.Location = new Point(270, btnTop - 44);
        applyBtn.Location = new Point(28, btnTop);
        applyStaticBtn.Location = new Point(270, btnTop);
        restoreBtn.Location = new Point(28, btnTop + 74);"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("preview row added")
