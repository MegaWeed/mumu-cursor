import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ================= Cfg: 彩蛋字段 =================
s = s.replace('    public string CustomBody = "", CustomItem = "";',
              '    public string CustomBody = "", CustomItem = "";\n'
              '    public bool EggOn = false;     // 彩蛋：默认关闭\n'
              '    public int EggKey = 0;         // 绑定的虚拟键码，0 = 没绑')

s = s.replace('case "CustomItem": c.CustomItem = v; break;',
              'case "CustomItem": c.CustomItem = v; break;\n'
              '                        case "EggOn": c.EggOn = v == "1"; break;\n'
              '                        case "EggKey": c.EggKey = int.Parse(v); break;')

s = s.replace('lines.Add("CustomItem=" + CustomItem);',
              'lines.Add("CustomItem=" + CustomItem);\n'
              '            lines.Add("EggOn=" + (EggOn ? "1" : "0"));\n'
              '            lines.Add("EggKey=" + EggKey);')

# ================= 造型 / 颜色 两行 =================
old_ptr = '''        // ---- 小指针
        Section(y, "① 小指针", "点击位置的那个尖"); y += 40;
        var pointerNames = new[] { new[] { "arrow", "箭头" }, new[] { "cross", "十字" }, new[] { "ring", "圆环" }, new[] { "diamond", "菱形" }, new[] { "move", "四向" } };
        for (int i = 0; i < pointerNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + pointerNames[i][0] + ".png"), Text = pointerNames[i][1], Location = new Point(16 + i * 80, y), Size = new Size(72, 70), Selected = C.Pointer == pointerNames[i][0] };
            string key = pointerNames[i][0];
            th.Click += (a, b) => { C.Pointer = key; RefreshThumbs(); Save(); };
            pointerThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 80;
'''
new_ptr = '''        // ---- ① 造型
        Section(y, "① 造型", "点击位置的那个尖长什么样"); y += 36;
        var shapeNames = new[] { new[] { "chevron", "雪佛龙" }, new[] { "arrow", "箭头" }, new[] { "cross", "十字" }, new[] { "ring", "圆环" }, new[] { "diamond", "菱形" }, new[] { "move", "四向" } };
        for (int i = 0; i < shapeNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + shapeNames[i][0] + "_" + C.PointerColor + ".png"), Text = shapeNames[i][1], Location = new Point(16 + i * 70, y), Size = new Size(64, 60), Selected = C.PointerShape == shapeNames[i][0] };
            string key = shapeNames[i][0];
            th.Click += (a, b) => { C.PointerShape = key; RefreshThumbs(); Save(); };
            pointerThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 68;

        // ---- ② 颜色
        Section(y, "② 颜色", "同一个造型换五种配色"); y += 36;
        var colorNames = new[] { new[] { "silver", "银" }, new[] { "gold", "金" }, new[] { "neon", "霓虹" }, new[] { "ink", "墨" }, new[] { "bubble", "泡泡" } };
        for (int i = 0; i < colorNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + C.PointerShape + "_" + colorNames[i][0] + ".png"), Text = colorNames[i][1], Location = new Point(16 + i * 70, y), Size = new Size(64, 58), Selected = C.PointerColor == colorNames[i][0] };
            string key = colorNames[i][0];
            th.Click += (a, b) => { C.PointerColor = key; RefreshThumbs(); Save(); };
            colorThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 66;
'''
assert old_ptr in s
s = s.replace(old_ptr, new_ptr)

s = s.replace('Section(y, "② 主体"', 'Section(y, "③ 主体"')
s = s.replace('Section(y, "③ 连接线"', 'Section(y, "④ 连接线"')
s = s.replace('Section(y, "④ 吊起物品"', 'Section(y, "⑤ 吊起物品"')
s = s.replace('Section(y, "左键点击"', 'Section(y, "⑥ 左键点击"')

# ================= 彩蛋栏 =================
old_tip = '''        var tip = new Label
        {'''
new_egg = '''        // ---- ⑦ 彩蛋
        Section(y, "⑦ 彩蛋", "绑一个键，按一下就放一段声音（默认关闭）"); y += 36;
        eggSwitch = new Switch { Text = "开启彩蛋", On = C.EggOn, Location = new Point(16, y), Size = new Size(150, 26) };
        eggSwitch.Click += (a, b) =>
        {
            C.EggOn = eggSwitch.On;
            if (!C.EggOn) { UnbindEgg(); }
            else if (C.EggKey != 0) BindEgg(C.EggKey);
            Save(); RefreshThumbs();
        };
        settings.Controls.Add(eggSwitch);

        eggBtn = new Btn { Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键", Location = new Point(176, y), Size = new Size(130, 26) };
        eggBtn.Click += (a, b) => StartBind();
        settings.Controls.Add(eggBtn);

        eggTest = new Btn { Text = "试听", Location = new Point(312, y), Size = new Size(76, 26) };
        eggTest.Click += (a, b) => { PlayEgg(); };
        settings.Controls.Add(eggTest);
        y += 32;

        eggHint = new Label
        {
            Text = "先点「绑定按键」，然后直接按下想用的键（建议 F6~F12）。\\n绑好后按一下试听，满意再开「启用」。",
            ForeColor = Color.FromArgb(128, 124, 142),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 34),
            Location = new Point(16, y),
            BackColor = Color.Transparent
        };
        settings.Controls.Add(eggHint);
        y += 40;

        var tip = new Label
        {'''
assert old_tip in s
s = s.replace(old_tip, new_egg, 1)

# ================= RefreshThumbs =================
s = s.replace('        foreach (var t in pointerThumbs) t.Selected = t.Text == NameOf(C.Pointer);',
'''        var shapeKeys = new[] { "chevron", "arrow", "cross", "ring", "diamond", "move" };
        var colorKeys = new[] { "silver", "gold", "neon", "ink", "bubble" };
        for (int i = 0; i < pointerThumbs.Count && i < shapeKeys.Length; i++)
        {
            pointerThumbs[i].Selected = C.PointerShape == shapeKeys[i];
            pointerThumbs[i].Pic = Art.Res("pointer_" + shapeKeys[i] + "_" + C.PointerColor + ".png");
        }
        for (int i = 0; i < colorThumbs.Count && i < colorKeys.Length; i++)
        {
            colorThumbs[i].Selected = C.PointerColor == colorKeys[i];
            colorThumbs[i].Pic = Art.Res("pointer_" + C.PointerShape + "_" + colorKeys[i] + ".png");
        }
        if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键";''')

p.write_text(s, encoding="utf-8")
print("egg ui patched", s.count("eggSwitch"), s.count("colorThumbs"))
