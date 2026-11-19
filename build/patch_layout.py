import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

start = s.index('        // ---- ① 造型')
end = s.index('        // ---- ③ 主体') if '        // ---- ③ 主体' in s else s.index('        Section(y, "③ 主体"')
new = '''        // ---- ① 小指针 = 造型 + 颜色（两行，共用一个小标题）
        Section(y, "① 小指针", "点击位置的那个尖：先挑造型，再挑颜色"); y += 38;
        var rowTag = new Label { Text = "造型", ForeColor = Color.FromArgb(150, 146, 164), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16, y + 20), BackColor = Color.Transparent };
        settings.Controls.Add(rowTag);

        var shapeNames = new[] { new[] { "chevron", "雪佛龙" }, new[] { "arrow", "箭头" }, new[] { "cross", "十字" }, new[] { "ring", "圆环" }, new[] { "diamond", "菱形" }, new[] { "move", "四向" } };
        for (int i = 0; i < shapeNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + shapeNames[i][0] + "_" + C.PointerColor + ".png"), Text = shapeNames[i][1], Location = new Point(52 + i * 64, y), Size = new Size(60, 56), Selected = C.PointerShape == shapeNames[i][0] };
            string key = shapeNames[i][0];
            th.Click += (a, b) => { C.PointerShape = key; RefreshThumbs(); Save(); };
            pointerThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 62;

        var colTag = new Label { Text = "颜色", ForeColor = Color.FromArgb(150, 146, 164), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16, y + 20), BackColor = Color.Transparent };
        settings.Controls.Add(colTag);

        var colorNames = new[] { new[] { "silver", "银" }, new[] { "gold", "金" }, new[] { "neon", "霓虹" }, new[] { "ink", "墨" }, new[] { "bubble", "泡泡" } };
        for (int i = 0; i < colorNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + C.PointerShape + "_" + colorNames[i][0] + ".png"), Text = colorNames[i][1], Location = new Point(52 + i * 64, y), Size = new Size(60, 56), Selected = C.PointerColor == colorNames[i][0] };
            string key = colorNames[i][0];
            th.Click += (a, b) => { C.PointerColor = key; RefreshThumbs(); Save(); };
            colorThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 66;

'''
s = s[:start] + new + s[end:]

# 段落间距 40 -> 34，主体/吊物行 104 -> 96
s = s.replace('            Section(y, "③ 主体", "挂件的身体，可以换图"); y += 40;', '        Section(y, "② 主体", "挂件的身体，可以换图"); y += 34;')
s = s.replace('        Section(y, "② 主体", "挂件的身体，可以换图"); y += 40;', '        Section(y, "② 主体", "挂件的身体，可以换图"); y += 34;')
s = s.replace('Section(y, "③ 主体", "挂件的身体，可以换图"); y += 40;', 'Section(y, "② 主体", "挂件的身体，可以换图"); y += 34;')
s = s.replace('Section(y, "④ 连接线", "那根把金币吊住的线"); y += 40;', 'Section(y, "③ 连接线", "那根把金币吊住的线"); y += 34;')
s = s.replace('Section(y, "⑤ 吊起物品", "绳子末端那个会跳的"); y += 40;', 'Section(y, "④ 吊起物品", "绳子末端那个会跳的"); y += 34;')
s = s.replace('Section(y, "⑥ 左键点击", "吊起物品跳一下 + 发光 + 音效"); y += 40;', 'Section(y, "⑤ 左键点击", "吊起物品跳一下 + 发光 + 音效"); y += 34;')
s = s.replace('Section(y, "⑦ 彩蛋", "绑一个键，按一下就放一段声音（默认关闭）"); y += 36;', 'Section(y, "⑥ 彩蛋", "绑一个键，按一下就放一段声音（默认关闭）"); y += 34;')
s = s.replace('        y += 104;\n\n        // ---- 连接线', '        y += 96;\n\n        // ---- 连接线')
s = s.replace('        y += 104;\n\n        // ---- 点击动画', '        y += 96;\n\n        // ---- 点击动画')

p.write_text(s, encoding="utf-8")
print("pointer rows compacted", s.count("rowTag"), s.count("Section(y, \"② 主体"))
