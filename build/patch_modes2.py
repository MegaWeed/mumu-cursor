import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert a in s, "NOT FOUND: " + a[:80]
    s = s.replace(a, b, n)


# 1) 右栏不再放模式选择器（高度会顶出屏幕），把两个按钮挪到左列
rep("""        bool stat = C.Mode == "static";
        int y = 12;

        // ---- 模式：动态挂件 / 静态贴图
        Section(y, "模式", "桌面用动态，打游戏用静态"); y += 30;
        var dynBtn = new Btn { Text = "动态挂件", Sub = "会晃，有物理手感", Primary = !stat, Location = new Point(16, y), Size = new Size(198, 48) };
        dynBtn.Click += (a, b) => SetMode("pendant");
        var stBtn = new Btn { Text = "静态贴图", Sub = "不晃，跟手，适合游戏", Primary = stat, Location = new Point(222, y), Size = new Size(198, 48) };
        stBtn.Click += (a, b) => SetMode("static");
        settings.Controls.Add(dynBtn); settings.Controls.Add(stBtn);
        y += 56;
""",
    """        bool stat = C.Mode == "static";
        int y = 14;
""")

# 2) 左列：预览卡下面加一行模式按钮
rep("""        hint = new Label
        {""",
    """        modeDyn = new Btn { Text = "动态挂件", Sub = "会晃，有物理手感", Primary = C.Mode != "static", Location = new Point(28, 0), Size = new Size(228, 50) };
        modeDyn.Click += (a, b) => SetMode("pendant");
        modeStatic = new Btn { Text = "静态贴图", Sub = "不晃、跟手，适合游戏", Primary = C.Mode == "static", Location = new Point(270, 0), Size = new Size(228, 50) };
        modeStatic.Click += (a, b) => SetMode("static");
        Controls.Add(modeDyn); Controls.Add(modeStatic);

        hint = new Label
        {""")

# 3) 左列排版：给模式按钮留出一行
rep("""    void LayoutLeft()
    {
        int btnTop = ClientSize.Height - 28 - 118;
        int cardH = btnTop - 12 - 96;
        if (cardH < 320) cardH = 320;
        leftCard.Size = new Size(470, cardH);
        preview.Size = new Size(470 - 24, cardH - 24);
        hint.Top = btnTop - 26;
        applyBtn.Location = new Point(28, btnTop);
        restoreBtn.Location = new Point(28, btnTop + 68);
    }""",
    """    void LayoutLeft()
    {
        int btnTop = ClientSize.Height - 28 - 118;
        int modeTop = btnTop - 60;
        int cardH = modeTop - 12 - 96;
        if (cardH < 320) cardH = 320;
        leftCard.Size = new Size(470, cardH);
        preview.Size = new Size(470 - 24, cardH - 24);
        hint.Top = modeTop - 26;
        modeDyn.Location = new Point(28, modeTop);
        modeStatic.Location = new Point(270, modeTop);
        applyBtn.Location = new Point(28, btnTop);
        restoreBtn.Location = new Point(28, btnTop + 68);
    }""")

# 4) 字段声明
rep("""    public int NeedH = 620;""",
    """    public int NeedH = 620;
    Btn modeDyn, modeStatic;""")

# 5) SetMode 里刷新按钮的选中态
rep("""        C.Mode = m;
        Save();
        FillSettings();""",
    """        C.Mode = m;
        Save();
        SyncModeButtons();
        FillSettings();""")

# 6) 统一刷新（RefreshThumbs 里也调一次，保证启动/切换后按钮态正确）
rep("""    void RefreshThumbs()
    {""",
    """    void SyncModeButtons()
    {
        if (modeDyn == null || modeStatic == null) return;
        modeDyn.Primary = C.Mode != "static";
        modeStatic.Primary = C.Mode == "static";
        modeDyn.Invalidate(); modeStatic.Invalidate();
    }

    void RefreshThumbs()
    {
        SyncModeButtons();""")

p.write_text(s, encoding="utf-8")
print("ok")
