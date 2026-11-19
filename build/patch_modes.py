import pathlib, re

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert a in s, "NOT FOUND: " + a[:70]
    s = s.replace(a, b, n)


# ---------------- 1. Cfg: Mode
rep("    public bool RopeOn = true;",
    "    public string Mode = \"pendant\";     // pendant = 动态挂件；static = 静态贴图（游戏用）\n    public bool RopeOn = true;")

rep("                case \"RopeOn\": c.RopeOn = v == \"1\"; break;",
    "                case \"RopeOn\": c.RopeOn = v == \"1\"; break;\n                case \"Mode\": c.Mode = v; break;")

rep("            lines.Add(\"RopeOn=\" + (RopeOn ? \"1\" : \"0\"));",
    "            lines.Add(\"RopeOn=\" + (RopeOn ? \"1\" : \"0\"));\n            lines.Add(\"Mode=\" + Mode);")

# ---------------- 2. Look: Static
rep("    public Bitmap Item; public int ItemW, ItemH;",
    "    public Bitmap Item; public int ItemW, ItemH;\n    public bool Static;        // true = 静态贴图模式：不画绳子、不画吊物，整张图跟手")

# ---------------- 3. Art.Build: static branch
rep("""        if (c.BodyKind == "avatar") l.Body = Resized(Res("body_avatar.png"), 110);""",
    """        if (c.Mode == "static")
        {
            l.Static = true;
            l.Body = Res("static_full.png");
            l.BodyOffX = 20f; l.BodyOffY = 14f;
            l.PivFx = 0.5f; l.PivFy = 0.5f;
            l.Item = Res("item_coin.png"); l.ItemW = l.Item.Width; l.ItemH = l.Item.Height;
            l.RopeOn = false; l.RopeGlow = false; l.ClickAnim = false; l.ClickSound = c.ClickSound;
            return l;
        }

        if (c.BodyKind == "avatar") l.Body = Resized(Res("body_avatar.png"), 110);""")

# ---------------- 4. Pendant.Update: static = 直接跟手，不晃
rep("""    public void Update(double dt)
    {
        acc += dt;""",
    """    public void Update(double dt)
    {
        if (L.Static)
        {
            // 静态模式不做弹簧跟随：游戏里哪怕 30ms 的拖影都会让人打不准
            x = tx; y = ty; vx = vy = 0; tilt = 0;
            Glow *= Math.Pow(0.006, dt);
            Pop *= Math.Pow(0.0009, dt);
            return;
        }
        acc += dt;""")

# ---------------- 5. Pendant.Draw: static 分支
rep("""    public void Draw(Graphics g, float ox, float oy)
    {
        if (L.RopeOn)""",
    """    public void Draw(Graphics g, float ox, float oy)
    {
        if (L.Static)
        {
            g.DrawImage(L.Body, ox + L.BodyOffX, oy + L.BodyOffY, L.Body.Width, L.Body.Height);
            g.DrawImage(L.Pointer, ox - L.HotX, oy - L.HotY);
            return;
        }

        if (L.RopeOn)""")

# ---------------- 6. 构造函数里的尺寸计算抽成 LayoutWindow()
rep("""        // 右栏内容有多高，窗口就有多高（放不下才滚动，尽量不出现滚动条）
        int want = 96 + NeedH + 26;
        int maxH = Screen.PrimaryScreen.WorkingArea.Height - 60;
        int h = Math.Max(700, Math.Min(want, maxH));
        ClientSize = new Size(1000, h);
        if (h < want)
        {
            int room = h - 96 - 26;
            shell.Size = new Size(438, room);
            settings.Size = new Size(434, room - 4);
            settings.AutoScroll = true;
        }
        LayoutLeft();
""",
    """        LayoutWindow();
""")

rep("""    void BuildHeader()""",
    """    // 右栏内容有多高，窗口就有多高（放不下才滚动，尽量不出现滚动条）
    void LayoutWindow()
    {
        int want = 96 + NeedH + 26;
        int maxH = Screen.PrimaryScreen.WorkingArea.Height - 60;
        int h = Math.Max(700, Math.Min(want, maxH));
        ClientSize = new Size(1000, h);
        shell.Location = new Point(514, 96);
        if (h < want)
        {
            int room = h - 96 - 26;
            shell.Size = new Size(438, room);
            settings.Size = new Size(434, room - 4);
            settings.AutoScroll = true;
        }
        else
        {
            shell.Size = new Size(438, NeedH);
            settings.Size = new Size(434, NeedH - 4);
            settings.AutoScroll = false;
        }
        LayoutLeft();
    }

    // 切换「动态 / 静态」：右栏要整套重建（静态没有③④）
    void SetMode(string m)
    {
        if (C.Mode == m) return;
        C.Mode = m;
        Save();
        FillSettings();
        LayoutWindow();
        RefreshThumbs();
        if (preview != null) preview.Rebuild(Art.Build(C));
        if (overlay != null) overlay.SetLook(Art.Build(C));
    }

    void BuildHeader()""")

# ---------------- 7. BuildRight 拆出 FillSettings，并加模式选择
rep("""        int y = 14;
        // ---- ① 小指针 = 造型 + 颜色（两行，共用一个小标题）""",
    """        FillSettings();
    }

    void FillSettings()
    {
        settings.Controls.Clear();
        pointerThumbs.Clear(); colorThumbs.Clear(); bodyThumbs.Clear();
        itemThumbs.Clear(); swatches.Clear(); sfxBtns.Clear();

        bool stat = C.Mode == "static";
        int y = 12;

        // ---- 模式：动态挂件 / 静态贴图
        Section(y, "模式", "桌面用动态，打游戏用静态"); y += 30;
        var dynBtn = new Btn { Text = "动态挂件", Sub = "会晃，有物理手感", Primary = !stat, Location = new Point(16, y), Size = new Size(198, 48) };
        dynBtn.Click += (a, b) => SetMode("pendant");
        var stBtn = new Btn { Text = "静态贴图", Sub = "不晃，跟手，适合游戏", Primary = stat, Location = new Point(222, y), Size = new Size(198, 48) };
        stBtn.Click += (a, b) => SetMode("static");
        settings.Controls.Add(dynBtn); settings.Controls.Add(stBtn);
        y += 56;

        // ---- ① 小指针 = 造型 + 颜色（两行，共用一个小标题）""")

# ---------------- 8. ② 主体：静态模式换成整张图
rep("""        Section(y, "② 主体", "挂件的身体，可以换图"); y += 30;""",
    """        if (stat)
        {
            Section(y, "② 整张图", "静态模式就用这一张，金币已经画在图里"); y += 30;
            var s1 = new Thumb { Pic = Art.Res("static_full.png"), Text = "静态图", Location = new Point(16, y), Size = new Size(110, 104), Selected = true };
            settings.Controls.Add(s1);
            y += 110;
        }
        else
        {
        Section(y, "② 主体", "挂件的身体，可以换图"); y += 30;""")

# ② 结束 + ③④ 只在动态模式出现
rep("""        y += 96;

        // ---- 连接线""",
    """        y += 96;
        }

        if (!stat)
        {
        // ---- 连接线""")

rep("""        y += 96;

        // ---- 点击动画""",
    """        y += 96;
        }

        // ---- 点击动画""")

# ---------------- 9. ⑤ 点击：静态模式没有动画开关，副标题也不一样
rep("""        Section(y, "⑤ 左键点击", "吊起物品跳一下 + 发光 + 音效"); y += 30;
        clickSwitch = new Switch { Text = "开启点击动画", On = C.ClickAnim, Location = new Point(16, y), Size = new Size(200, 26) };
        clickSwitch.Click += (a, b) => { C.ClickAnim = clickSwitch.On; Save(); };
        settings.Controls.Add(clickSwitch);
        soundSwitch = new Switch { Text = "点击音效", On = C.ClickSound, Location = new Point(226, y), Size = new Size(170, 26) };""",
    """        Section(y, "⑤ 左键点击", stat ? "静态模式只放音效" : "吊起物品跳一下 + 发光 + 音效"); y += 30;
        if (!stat)
        {
            clickSwitch = new Switch { Text = "开启点击动画", On = C.ClickAnim, Location = new Point(16, y), Size = new Size(200, 26) };
            clickSwitch.Click += (a, b) => { C.ClickAnim = clickSwitch.On; Save(); };
            settings.Controls.Add(clickSwitch);
        }
        soundSwitch = new Switch { Text = "点击音效", On = C.ClickSound, Location = new Point(stat ? 16 : 226, y), Size = new Size(170, 26) };""")

p.write_text(s, encoding="utf-8")
print("patched ok")
