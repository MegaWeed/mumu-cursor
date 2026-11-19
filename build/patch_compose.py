import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- Cfg.CursorSize ----------
old = "    public bool ClickSound = true;"
new = """    public bool ClickSound = true;
    public int CursorSize = 128;      // 静态模式的真光标尺寸（32~256），Windows 会照这个大小画"""
assert old in s
s = s.replace(old, new, 1)

old = """        case "ClickSound": c.ClickSound = v == "1"; break;"""
new = """        case "ClickSound": c.ClickSound = v == "1"; break;
        case "CursorSize": c.CursorSize = Math.Max(32, Math.Min(256, int.Parse(v))); break;"""
assert old in s
s = s.replace(old, new, 1)

old = """        lines.Add("ClickSound=" + (ClickSound ? "1" : "0"));"""
new = """        lines.Add("ClickSound=" + (ClickSound ? "1" : "0"));
        lines.Add("CursorSize=" + CursorSize);"""
assert old in s
s = s.replace(old, new, 1)

# ---------- Look 增加合成图 ----------
old = """    public bool Static;        // true = 静态贴图模式：不画绳子、不画吊物，整张图跟手"""
new = """    public bool Static;        // true = 静态贴图模式：不画绳子、不画吊物，整张图跟手
    public Bitmap StaticCur;   // 静态模式真正的光标图（小指针 + 主体 合成，N×N）
    public int StaticHotX, StaticHotY;"""
assert old in s
s = s.replace(old, new, 1)

# ---------- 静态 Build：合成 ----------
old = """            l.RopeOn = false; l.RopeGlow = false; l.ClickAnim = false; l.ClickSound = c.ClickSound;
            return l;"""
new = """            l.RopeOn = false; l.RopeGlow = false; l.ClickAnim = false; l.ClickSound = c.ClickSound;
            int hx, hy;
            l.StaticCur = CurArt.Compose(l.Body, l.Pointer, l.HotX, l.HotY, c.CursorSize, out hx, out hy);
            l.StaticHotX = hx; l.StaticHotY = hy;
            return l;"""
assert old in s
s = s.replace(old, new, 1)

# ---------- Draw 静态：只画合成图 ----------
old = """        if (L.Static)
        {
            g.DrawImage(L.Body, ox + L.BodyOffX, oy + L.BodyOffY, L.Body.Width, L.Body.Height);
            g.DrawImage(L.Pointer, ox - L.HotX, oy - L.HotY);
            return;
        }"""
new = """        if (L.Static)
        {
            // 预览画的就是光标本身（同一张合成图），所见即所得
            if (L.StaticCur == null) return;
            float k = (float)(L.StaticCur.Width * 2.2) / L.StaticCur.Width;   // 预览放大一点才看得清
            float w = L.StaticCur.Width * 2.2f;
            g.DrawImage(L.StaticCur, ox - w / 2f, oy - w / 2f, w, w);
            return;
        }"""
assert old in s
s = s.replace(old, new, 1)

# ---------- CurArt：合成器 ----------
old = "// ================================================================ 素材"
new = """// ================================================================ 真光标合成
static class CurArt
{
    // 把小指针 + 主体合成一张 N×N 的光标图（热点就是小指针的尖/中心）
    public static Bitmap Compose(Bitmap body, Bitmap pointer, float hotX, float hotY, int size, out int hx, out int hy)
    {
        var bmp = new Bitmap(size, size);
        using (var g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.Clear(Color.Transparent);

            // 主体：按比例放进 0.92 见方，底部稍留空
            float box = size * 0.92f;
            float bw = body.Width, bh = body.Height;
            float k = Math.Min(box / bw, box / bh);
            float dw = bw * k, dh = bh * k;
            g.DrawImage(body, (size - dw) / 2f, size * 0.05f, dw, dh);

            // 小指针：素材是 43px 的方图，按 0.42×N 的比例缩放
            float ps = size * 0.42f / 43f;
            float px = size * 0.16f, py = size * 0.20f;
            g.DrawImage(pointer, px - hotX * ps, py - hotY * ps, pointer.Width * ps, pointer.Height * ps);

            hx = (int)Math.Round(px); hy = (int)Math.Round(py);
        }
        return bmp;
    }
}

// ================================================================ 素材"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("cursor composition added")
