import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- 1) 固定窗口高度：无论哪个模式都按「动态」的内容高度算 ----------
old = """    void LayoutWindow()
    {
        int want = 96 + NeedH + 26;"""
new = """    const int StableNeedH = 887;    // 动态模式的内容高度；静态模式内容更少，但窗口不准变矮

    void LayoutWindow()
    {
        int need = Math.Max(NeedH, StableNeedH);
        int want = 96 + need + 26;"""
assert old in s, "LayoutWindow head"
s = s.replace(old, new, 1)

old = """            shell.Size = new Size(438, NeedH);
            settings.Size = new Size(434, NeedH - 4);"""
new = """            shell.Size = new Size(438, need);
            settings.Size = new Size(434, need - 4);"""
assert old in s, "LayoutWindow else"
s = s.replace(old, new, 1)

# ---------- 2) 切换模式时淡入淡出 ----------
old = """    void SetMode(string m)
    {
        if (C.Mode == m) return;
        C.Mode = m;
        Save();
        SyncModeButtons();
        FillSettings();
        LayoutWindow();
        RefreshThumbs();
        if (preview != null) preview.Rebuild(Art.Build(C));
        if (overlay != null) overlay.SetLook(Art.Build(C));
    }"""
new = """    void SetMode(string m)
    {
        if (C.Mode == m) return;
        C.Mode = m;
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
        if (snap != null) FadeOut(snap);
    }

    // 把旧画面盖在新内容上，逐帧降透明度（ImageAttributes + ColorMatrix 的 alpha 行）
    void FadeOut(Bitmap snap)
    {
        try
        {
            var host = settings.Parent;
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

            int frame = 0;
            const int total = 11;
            var t = new System.Windows.Forms.Timer { Interval = 16 };
            t.Tick += (a, b) =>
            {
                frame++;
                float a2 = 1f - (float)frame / total;
                if (a2 <= 0.02f)
                {
                    t.Stop(); t.Dispose();
                    host.Controls.Remove(pic);
                    pic.Dispose();
                    snap.Dispose();
                    return;
                }
                var faded = new Bitmap(snap.Width, snap.Height);
                using (var g = Graphics.FromImage(faded))
                using (var ia = new System.Drawing.Imaging.ImageAttributes())
                {
                    var cm = new System.Drawing.Imaging.ColorMatrix();
                    cm.Matrix33 = a2;
                    ia.SetColorMatrix(cm, System.Drawing.Imaging.ColorMatrixFlag.Default, System.Drawing.Imaging.ColorAdjustType.Bitmap);
                    g.DrawImage(snap, new Rectangle(0, 0, snap.Width, snap.Height), 0, 0, snap.Width, snap.Height, GraphicsUnit.Pixel, ia);
                }
                var old = pic.Image;
                pic.Image = faded;
                if (old != null && old != snap) old.Dispose();
            };
            t.Start();
        }
        catch { }
    }"""
assert old in s, "SetMode body"
s = s.replace(old, new, 1)

# ---------- 3) 两个模式按钮的副标题改成直白说法 ----------
old = 'modeDyn = new Btn { Text = "动态挂件", Sub = "会晃，有物理手感",'
new = 'modeDyn = new Btn { Text = "动态挂件", Sub = "有动画，桌面用",'
assert old in s
s = s.replace(old, new, 1)

old = 'modeStatic = new Btn { Text = "静态贴图", Sub = "不晃、跟手，适合游戏",'
new = 'modeStatic = new Btn { Text = "静态贴图", Sub = "打游戏用",'
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("patched: fixed height + fade + labels")
