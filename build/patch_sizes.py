import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = '''            Section(y, "② 整张图", "这张图会做成真正的系统光标（32×32），金币已经画在图里"); y += 30;
            var s1 = new Thumb { Pic = Art.Res("static_full.png"), Text = "静态图", Location = new Point(16, y), Size = new Size(110, 104), Selected = true };
            settings.Controls.Add(s1);
            y += 110;'''
new = '''            Section(y, "② 整张图", "上面选的小指针 + 这张图，合成真正的系统光标"); y += 30;
            var s1 = new Thumb { Pic = Art.Res("static_full.png"), Text = "静态图", Location = new Point(16, y), Size = new Size(110, 104), Selected = true };
            settings.Controls.Add(s1);
            y += 110;

            // 光标尺寸：Windows 允许 32~256，选多大就按多大画
            var sizeLab = new Label { Text = "光标大小", ForeColor = Color.FromArgb(178, 182, 195), BackColor = Color.Transparent, AutoSize = true, Location = new Point(16, y + 4) };
            settings.Controls.Add(sizeLab);
            int cx = 88;
            foreach (int px in new int[] { 32, 48, 64, 96, 128, 192, 256 })
            {
                int val = px;
                var chip = new Btn
                {
                    Text = px.ToString(),
                    Sub = "",
                    Primary = C.CursorSize == val,
                    Location = new Point(cx, y),
                    Size = new Size(px >= 128 ? 56 : 40, 30)
                };
                chip.Click += (a, b) =>
                {
                    C.CursorSize = val;
                    Save();
                    FillSettings();
                    RefreshThumbs();
                    if (staticOn) Apply();
                };
                settings.Controls.Add(chip);
                cx += chip.Width + 6;
            }
            y += 36;
            var sizeHint = new Label
            {
                Text = "越大越清楚，但也越占屏幕（128 是推荐值）",
                ForeColor = Color.FromArgb(150, 154, 168),
                BackColor = Color.Transparent,
                AutoSize = false,
                Size = new Size(390, 18),
                Location = new Point(16, y)
            };
            settings.Controls.Add(sizeHint);
            y += 30;'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("size chips added")
