import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- Section：副标题改到标题同一行 ----------
old = '''        var l = new Label { Text = title, ForeColor = Color.FromArgb(240, 236, 250), Font = new Font("Microsoft YaHei UI", 10.5f, FontStyle.Bold), AutoSize = true, Location = new Point(16, y), BackColor = Color.Transparent };
        settings.Controls.Add(l);
        if (!string.IsNullOrEmpty(sub))
        {
            var s = new Label { Text = sub, ForeColor = Color.FromArgb(130, 126, 144), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16, y + 24), BackColor = Color.Transparent };
            settings.Controls.Add(s);
        }'''
new = '''        var l = new Label { Text = title, ForeColor = Color.FromArgb(240, 236, 250), Font = new Font("Microsoft YaHei UI", 10.5f, FontStyle.Bold), AutoSize = true, Location = new Point(16, y - 2), BackColor = Color.Transparent };
        settings.Controls.Add(l);
        if (!string.IsNullOrEmpty(sub))
        {
            // 副标题跟标题同一行，省掉一行高度（原来会和下面的卡片/开关重叠）
            int w = TextRenderer.MeasureText(title, l.Font).Width;
            var s = new Label { Text = sub, ForeColor = Color.FromArgb(126, 122, 142), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16 + w + 12, y + 7), BackColor = Color.Transparent };
            settings.Controls.Add(s);
        }'''
assert old in s
s = s.replace(old, new)

# ---------- 内容起始位置 34/38 -> 30 ----------
s = s.replace('Section(y, "① 小指针", "点击位置的那个尖：先挑造型，再挑颜色"); y += 38;',
              'Section(y, "① 小指针", "先挑造型，再挑颜色"); y += 30;')
for t in ['② 主体', '③ 连接线', '④ 吊起物品', '⑤ 左键点击', '⑥ 彩蛋']:
    s = s.replace(f'Section(y, "{t}"', f'Section(y, "{t}"')
s = s.replace('y += 34;', 'y += 30;')

p.write_text(s, encoding="utf-8")
print("section inline", s.count('y += 30;'))
