import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 去掉调试用的 fade_snap 落盘
dbg = '            try { snap.Save(Path.Combine(Path.GetTempPath(), "fade_snap.png"), System.Drawing.Imaging.ImageFormat.Png); } catch { }\n'
s = s.replace(dbg, "", 1)

# 2) tip 存成字段，方便贴底
s = s.replace("        var tip = new Label\n        {", "        tipLabel = new Label\n        {", 1)
s = s.replace("        settings.Controls.Add(tip);", "        settings.Controls.Add(tipLabel);", 1)

# 3) LayoutWindow 末尾把提示贴到面板底部（静态模式内容少，底下不至于空一大块）
old = "        LayoutLeft();\n    }\n\n    // 切换「动态 / 静态」"
new = ("        LayoutLeft();\n"
       "        if (tipLabel != null) tipLabel.Top = Math.Max(0, settings.Height - 42);   // 提示永远贴底\n"
       "    }\n\n    // 切换「动态 / 静态」")
assert old in s, "LayoutWindow tail"
s = s.replace(old, new, 1)

# 4) 字段声明
old2 = "    int NeedHDynamic;"
new2 = "    int NeedHDynamic;\n    Label tipLabel;"
assert old2 in s
s = s.replace(old2, new2, 1)

p.write_text(s, encoding="utf-8")
print("tip pinned to bottom")
