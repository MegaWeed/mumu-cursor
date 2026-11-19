import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- 1) 合成布局：小指针放到左上角、主体往右下让开，热点=指针尖 ----------
old = """            // 主体：按比例放进 0.92 见方，底部稍留空
            float box = size * 0.92f;
            float bw = body.Width, bh = body.Height;
            float k = Math.Min(box / bw, box / bh);
            float dw = bw * k, dh = bh * k;
            g.DrawImage(body, (size - dw) / 2f, size * 0.05f, dw, dh);

            // 小指针：素材是 43px 的方图，按 0.42×N 的比例缩放
            float ps = size * 0.42f / 43f;
            float px = size * 0.16f, py = size * 0.20f;
            g.DrawImage(pointer, px - hotX * ps, py - hotY * ps, pointer.Width * ps, pointer.Height * ps);

            hx = (int)Math.Round(px); hy = (int)Math.Round(py);"""
new = """            // 主体：占右下角 0.64 见方，左上角留给小指针，两者不重叠
            float box = size * 0.64f;
            float bw = body.Width, bh = body.Height;
            float k = Math.Min(box / bw, box / bh);
            float dw = bw * k, dh = bh * k;
            g.DrawImage(body, size - dw - size * 0.02f, size - dh - size * 0.02f, dw, dh);

            // 小指针：方图 43px，按 0.34×N 缩放，尖（热点）落在左上角 (0.12N, 0.12N)
            float ps = size * 0.34f / 43f;
            float px = size * 0.12f, py = size * 0.12f;
            g.DrawImage(pointer, px - hotX * ps, py - hotY * ps, pointer.Width * ps, pointer.Height * ps);

            hx = (int)Math.Round(px); hy = (int)Math.Round(py);"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 2) 去掉顶部两个模式开关按钮 ----------
old = "        Controls.Add(modeDyn); Controls.Add(modeStatic);"
new = "        // 模式不再用并列开关：直接由下面两个「变身」按钮决定，避免“选了没生效”的困惑"
assert old in s
s = s.replace(old, new, 1)

# ---------- 3) 变身按钮拆成两个 ----------
old = """        applyBtn = new Btn { Text = "变身为 MUMU 光标", Sub = "只换普通箭头，其它光标不动", Location = new Point(28, 598), Size = new Size(470, 60) };"""
new = """        applyBtn = new Btn { Text = "变身为动态挂件", Sub = "会晃，桌面用", Location = new Point(28, 596), Size = new Size(228, 66) };
        applyStaticBtn = new Btn { Text = "变身为静态光标", Sub = "真指针，游戏用", Location = new Point(270, 596), Size = new Size(228, 66) };"""
assert old in s
s = s.replace(old, new, 1)

old = """        applyBtn.Click += (a, b) => Apply();"""
new = """        applyBtn.Click += (a, b) => { if (C.Mode != "pendant") SetMode("pendant"); Apply(); };
        applyStaticBtn.Click += (a, b) => { if (C.Mode != "static") SetMode("static"); Apply(); };
        Controls.Add(applyStaticBtn);"""
assert old in s
s = s.replace(old, new, 1)

# 恢复按钮下移一点，给两个变身按钮腾地方
old = """        restoreBtn = new Btn { Text = "恢复系统光标", Sub = "装回你变身前的那一只", Primary = false, Location = new Point(28, 666), Size = new Size(470, 50) };"""
new = """        restoreBtn = new Btn { Text = "恢复系统光标", Sub = "装回你变身前的那一只", Primary = false, Location = new Point(28, 672), Size = new Size(470, 50) };"""
assert old in s
s = s.replace(old, new, 1)

# 字段
old = "    public Btn applyBtn, restoreBtn"
if old in s:
    s = s.replace(old, "    public Btn applyBtn, applyStaticBtn, restoreBtn", 1)
else:
    i = s.index("applyBtn")
p.write_text(s, encoding="utf-8")
print("buttons split + compose layout fixed")
