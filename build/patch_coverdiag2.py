import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """                cover = new PictureBox
                {
                    Image = snap,
                    SizeMode = PictureBoxSizeMode.Normal,
                    Bounds = new Rectangle(settings.Left, settings.Top, settings.Width, settings.Height),
                    Enabled = false
                };"""
new = """                cover = new PictureBox
                {
                    Image = snap,
                    SizeMode = PictureBoxSizeMode.Normal,
                    Bounds = new Rectangle(settings.Left, settings.Top, settings.Width, settings.Height),
                    Enabled = false,
                    Visible = true
                };"""
assert old in s
s = s.replace(old, new, 1)

# 测试用：把快照和当前面板都存下来，确认拍摄到的是「旧内容」
old2 = """                settings.Parent.Controls.Add(cover);
                cover.BringToFront();"""
new2 = """                settings.Parent.Controls.Add(cover);
                cover.BringToFront();
                if (Environment.GetEnvironmentVariable("MUMU_FADE_DEBUG") == "1")
                {
                    snap.Save(Path.Combine(Path.GetTempPath(), "fade_snap_" + m + ".png"), System.Drawing.Imaging.ImageFormat.Png);
                    Console.WriteLine("snap saved, zorder shell=" + settings.Parent.Controls.Count + " coverIdx=" + settings.Parent.Controls.GetChildIndex(cover) + " settingsIdx=" + settings.Parent.Controls.GetChildIndex(settings));
                }"""
assert old2 in s
s = s.replace(old2, new2, 1)
p.write_text(s, encoding="utf-8")
print("diagnostics v2")
