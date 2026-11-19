import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, 1)


# 1) 点击发光：弹跳减半保留，但光晕恢复并加强（并加一圈扩散的亮环）
rep('''        Glow = 0.6; Pop = 0.5;''',
'''        Glow = 1.0; Pop = 0.5;''')

rep('''        Glow *= Math.Pow(0.0025, dt);''',
'''        Glow *= Math.Pow(0.006, dt);''')

rep('''        if (Pop > 0.02)
        {
            float r = Math.Max(L.ItemW, L.ItemH) * (0.60f + 0.22f * (float)Pop);
            using (var path = new GraphicsPath())
            {
                path.AddEllipse(ix - r, iy + L.ItemH * 0.35f - r, r * 2, r * 2);
                using (var b = new PathGradientBrush(path))
                {
                    b.CenterColor = Color.FromArgb((int)(96 * Pop), 255, 236, 160);
                    b.SurroundColors = new[] { Color.FromArgb(0, 255, 220, 150) };
                    g.FillPath(b, path);
                }
            }
        }''',
'''        // 点击：暖色光晕 + 一圈往外扩的亮环
        if (Glow > 0.02)
        {
            float baseR = Math.Max(L.ItemW, L.ItemH);
            float r = baseR * (0.52f + 0.30f * (float)Glow);
            using (var path = new GraphicsPath())
            {
                path.AddEllipse(ix - r, iy + L.ItemH * 0.30f - r, r * 2, r * 2);
                using (var b = new PathGradientBrush(path))
                {
                    b.CenterColor = Color.FromArgb((int)(170 * Glow), 255, 240, 175);
                    b.SurroundColors = new[] { Color.FromArgb(0, 255, 210, 130) };
                    g.FillPath(b, path);
                }
            }
            float ringR = baseR * (0.55f + 1.05f * (float)(1 - Glow));
            using (var pen = new Pen(Color.FromArgb((int)(150 * Glow), 255, 226, 140), 2.2f))
                g.DrawEllipse(pen, ix - ringR, iy + L.ItemH * 0.30f - ringR, ringR * 2, ringR * 2);
        }''')

p.write_text(s, encoding="utf-8")
print("glow strengthened")
