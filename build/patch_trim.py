import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """            // 主体：占右下角 0.64 见方，左上角留给小指针，两者不重叠
            float box = size * 0.70f;
            float bw = body.Width, bh = body.Height;
            float k = Math.Min(box / bw, box / bh);
            float dw = bw * k, dh = bh * k;
            g.DrawImage(body, size - dw - size * 0.03f, size - dh - size * 0.03f, dw, dh);"""
new = """            // 主体：先裁掉四周的透明边（否则人物在画布里显得很小），再放进右下角
            Rectangle src = TrimAlpha(body);
            float box = size * 0.76f;
            float bw = src.Width, bh = src.Height;
            float k = Math.Min(box / bw, box / bh);
            float dw = bw * k, dh = bh * k;
            g.DrawImage(body, new RectangleF(size - dw - size * 0.02f, size - dh - size * 0.02f, dw, dh),
                        src.X, src.Y, src.Width, src.Height, GraphicsUnit.Pixel);"""
assert old in s
s = s.replace(old, new, 1)

helper = """
    // 找出有像素的范围（透明边裁掉），用小图采样，够快也够准
    static Rectangle TrimAlpha(Bitmap b)
    {
        int sw = 64, sh = 64;
        int minX = sw, minY = sh, maxX = -1, maxY = -1;
        for (int y = 0; y < sh; y++)
            for (int x = 0; x < sw; x++)
            {
                var c = b.GetPixel(x * b.Width / sw, y * b.Height / sh);
                if (c.A > 24)
                {
                    if (x < minX) minX = x; if (x > maxX) maxX = x;
                    if (y < minY) minY = y; if (y > maxY) maxY = y;
                }
            }
        if (maxX < 0) return new Rectangle(0, 0, b.Width, b.Height);
        int pad = 2;
        int x0 = Math.Max(0, (minX - pad) * b.Width / sw);
        int y0 = Math.Max(0, (minY - pad) * b.Height / sh);
        int x1 = Math.Min(b.Width, (maxX + 1 + pad) * b.Width / sw);
        int y1 = Math.Min(b.Height, (maxY + 1 + pad) * b.Height / sh);
        return Rectangle.FromLTRB(x0, y0, x1, y1);
    }
"""
anchor = "    // 把小指针 + 主体合成一张 N×N 的光标图（热点就是小指针的尖/中心）"
assert anchor in s
s = s.replace(anchor, helper + "\n" + anchor, 1)

p.write_text(s, encoding="utf-8")
print("alpha trim added")
