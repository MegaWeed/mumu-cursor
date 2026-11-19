import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- A) 提示行从「设置面板里」挪到「卡片上」，永远贴卡片底部，滚动也不影响 ----------
old = '''        tipLabel = new Label
        {
            Text = "提示：只换普通箭头这一个光标，变身前会自动备份。",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 20),
            Location = new Point(16, y),
            BackColor = Color.Transparent
        };
        settings.Controls.Add(tipLabel);
        y += 26;
'''
new = ""
assert old in s, "tip block"
s = s.replace(old, new, 1)

# 在构造里（shell/settings 建好之后）创建 tip，挂到 shell
old = '''        settings = new Panel { Location = new Point(2, 2), Size = new Size(434, 620), AutoScroll = false, BackColor = Color.FromArgb(30, 29, 38) };
        shell.Controls.Add(settings);
'''
new = '''        settings = new Panel { Location = new Point(2, 2), Size = new Size(434, 620), AutoScroll = false, BackColor = Color.FromArgb(30, 29, 38) };
        shell.Controls.Add(settings);

        tipLabel = new Label
        {
            Text = "提示：只换普通箭头这一个光标，变身前会自动备份。",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(410, 20),
            BackColor = Color.Transparent
        };
        shell.Controls.Add(tipLabel);
        tipLabel.BringToFront();
'''
assert old in s, "shell/settings block"
s = s.replace(old, new, 1)

# 位置：贴卡片底部（LayoutWindow 里）
old = '''        if (tipLabel != null) tipLabel.Top = Math.Max(0, settings.Height - 42);   // 提示永远贴底'''
new = '''        if (tipLabel != null) tipLabel.Location = new Point(16, Math.Max(0, shell.Height - 30));   // 贴卡片底部，不随面板滚动'''
assert old in s, "tip pin"
s = s.replace(old, new, 1)

# 面板再让出 26px，别被提示行压住
old = '''            shell.Size = new Size(438, need);
            settings.Size = new Size(434, need - 4);'''
new = '''            shell.Size = new Size(438, need);
            settings.Size = new Size(434, need - 30);'''
assert old in s, "settings size"
s = s.replace(old, new, 1)

# ---------- B) 切换动画不再先闪一下：先盖住旧画面，再重建 ----------
old = '''        C.Mode = m;
        Save();
        SyncModeButtons();

        // 先给右栏拍张快照，重建之后用它做一次 180ms 的淡出，切换就不会「啪」一下
        Bitmap snap = null;
        try
        {
            snap = new Bitmap(settings.Width, settings.Height);
            settings.DrawToBitmap(snap, new Rectangle(0, 0, settings.Width, settings.Height));
        }
        catch { if (snap != null) { snap.Dispose(); snap = null; } }

        FillSettings();
        LayoutWindow();
        RefreshThumbs();
        if (preview != null) preview.Rebuild(Art.Build(C));
        if (overlay != null) overlay.SetLook(Art.Build(C));
        if (snap != null) FadeOut(snap);'''
new = '''        // 先把旧画面拍下来、立刻盖在上面，然后再重建内容：
        // 顺序反了的话，用户会先看到新内容闪一帧，再开始淡出。
        Bitmap snap = null;
        PictureBox cover = null;
        try
        {
            if (settings.Width > 0 && settings.Height > 0)
            {
                snap = new Bitmap(settings.Width, settings.Height);
                settings.DrawToBitmap(snap, new Rectangle(0, 0, settings.Width, settings.Height));
                cover = new PictureBox
                {
                    Image = snap,
                    SizeMode = PictureBoxSizeMode.Normal,
                    Bounds = new Rectangle(settings.Left, settings.Top, settings.Width, settings.Height),
                    Enabled = false
                };
                settings.Parent.Controls.Add(cover);
                cover.BringToFront();
            }
        }
        catch { if (cover != null) { cover.Parent?.Controls.Remove(cover); cover.Dispose(); cover = null; } }

        C.Mode = m;
        Save();
        SyncModeButtons();
        FillSettings();
        LayoutWindow();
        RefreshThumbs();
        if (preview != null) preview.Rebuild(Art.Build(C));
        if (overlay != null) overlay.SetLook(Art.Build(C));
        if (tipLabel != null) tipLabel.BringToFront();
        if (cover != null) StartFade(cover, snap);'''
assert old in s, "SetMode body"
s = s.replace(old, new, 1)

# FadeOut(snap) → StartFade(cover, snap)：直接淡已有控件，不再自建
old = '''    // 把旧画面盖在新内容上，逐帧降透明度（ImageAttributes + ColorMatrix 的 alpha 行）
    void FadeOut(Bitmap snap)'''
new = '''    // 逐帧降透明度（ImageAttributes + ColorMatrix 的 alpha 行）
    void StartFade(PictureBox pic, Bitmap snap)'''
assert old in s, "FadeOut head"
s = s.replace(old, new, 1)

old = '''            var host = settings.Parent;
            if (host == null) { snap.Dispose(); return; }
            var pic = new PictureBox
            {
                Image = snap,
                SizeMode = PictureBoxSizeMode.Normal,
                Bounds = new Rectangle(settings.Left, settings.Top, settings.Width, settings.Height),
                Enabled = false
            };
            host.Controls.Add(pic);
            pic.BringToFront();

            int frame = 0;'''
new = '''            var host = pic.Parent;
            if (host == null) { snap.Dispose(); return; }

            int frame = 0;'''
assert old in s, "FadeOut body"
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("tip moved to shell + no-flash fade")
